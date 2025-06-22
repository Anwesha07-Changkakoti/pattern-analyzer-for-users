from dotenv import load_dotenv
import os

load_dotenv()
firebase_key = os.getenv("FIREBASE_KEY")

from fastapi import FastAPI, UploadFile, File, Depends, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder

import pandas as pd
import numpy as np
import uuid
import io
from pathlib import Path
from typing import Dict, List

from app.services.ml_model import detect_anomalies
from app.services.feature_engineering import preprocess
from sqlalchemy.orm import Session
from app.database import get_db            # <-- make sure import exists
from app.models import AnalysisResult
from app.models import Base
from app.database import engine
from app.routes.results import router as results_router
from app.routes.sessions import router as session_router 
import logging
import asyncio
import datetime
import random

from app.utils.firebase_auth import (
    get_current_user,
    get_current_user_optional_ws,
)

Base.metadata.create_all(bind=engine)

# Logging
logger = logging.getLogger("user-pattern-analyzer")
logging.basicConfig(level=logging.INFO)

# Local storage for CSV downloads and tracking
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# In-memory stores
ANOMALY_STORE: Dict[str, pd.DataFrame] = {}
CLICK_STORE: List[Dict] = []
SESSION_STORE: List[Dict] = []
NAV_PATHS: List[Dict] = []

app = FastAPI(title="User Pattern Analyzer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://pattern-analyzer-for-u-git-409984-anwesha-changkakotis-projects.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(results_router)
app.include_router(session_router) 

@app.post("/upload-click-logs")
async def upload_click_logs(file: UploadFile = File(...), user: Dict = Depends(get_current_user)):
    raw_bytes = await file.read()
    filename = file.filename or "uploaded"

    try:
        if filename.endswith(".json"):
            df = pd.read_json(io.BytesIO(raw_bytes))
        else:
            df = pd.read_csv(io.BytesIO(raw_bytes))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Error parsing file: {exc}")

    # --- 📍 Custom Mapping Logic
    # Attempt to create x, y coordinates from columns like Port, Bytes, etc.
    if not {"x", "y"}.issubset(df.columns):
        df = df.reset_index()  # fallback index as 'y'
        df["x"] = df["Port"] if "Port" in df.columns else df["index"] * 10  # Example logic
        df["y"] = df["Bytes"] if "Bytes" in df.columns else df["index"] * 5

    # Normalize or clip values for realistic viewport sizes
    df["x"] = df["x"].astype(float).clip(0, 1200)
    df["y"] = df["y"].astype(float).clip(0, 600)
    df["timestamp"] = pd.Timestamp.now().value // 1_000_000  # fallback timestamp

    for _, row in df.iterrows():
        if pd.notna(row["x"]) and pd.notna(row["y"]):
            CLICK_STORE.append({
                "x": float(row["x"]),
                "y": float(row["y"]),
                "timestamp": int(row.get("timestamp", pd.Timestamp.now().value // 1_000_000)),
                "pathname": "/uploaded"
            })

    return {"status": "clicks extracted", "count": len(df)}

@app.get("/test-auth")
async def test_auth_route(user: Dict = Depends(get_current_user)):
    return {"message": "Authenticated!", "user": user}

@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    user: Dict       = Depends(get_current_user),
    db:  Session     = Depends(get_db),     # ✅ inject DB session
):
    raw_bytes = await file.read()
    filename   = file.filename or "uploaded"

    # ---------- parse ----------------------------------------------------
    try:
        if filename.endswith(".json"):
            df_raw = pd.read_json(io.BytesIO(raw_bytes))
        else:
            df_raw = pd.read_csv(io.BytesIO(raw_bytes))
    except Exception as exc:
        logger.exception("Failed to parse file")
        raise HTTPException(400, f"Failed to parse file: {exc}")

    # ---------- predict anomalies ---------------------------------------
    df_proc = preprocess(df_raw)
    preds, reasons = detect_anomalies(
        df_raw=df_proc,
        user_uid=user["uid"],
        file_name=filename,
        return_reasons=True,
    )

    df_out               = df_raw.copy()
    df_out["anomaly"]    = preds
    df_out["anomaly_reason"] = reasons

    summary = {
        "total":      len(df_out),
        "anomalies":  int((df_out["anomaly"] == 1).sum()),
        "normal":     int((df_out["anomaly"] == 0).sum()),
    }

    # ---------- store anomalies in-memory & on disk ----------------------
    file_id = str(uuid.uuid4())
    ANOMALY_STORE[file_id] = df_out[df_out["anomaly"] == 1].copy()

    # ---------- ✅  save result metadata to DB  --------------------------
    db.add(
        AnalysisResult(
            user_id       = user["uid"],
            file_id       = file_id,              # allows download later
            file_name     = filename,
            total_records = summary["total"],
            anomaly_count = summary["anomalies"],
            timestamp     = datetime.datetime.utcnow(),
        )
    )
    db.commit()

    # ---------- build response ------------------------------------------
    df_json_safe  = df_out.replace({np.nan: None}).to_dict(orient="records")
    numeric_cols  = df_out.select_dtypes(include="number").columns.tolist()
    x_col, y_col  = numeric_cols[:2] if len(numeric_cols) >= 2 else (None, None)
    heatmap_points = (
        df_out[df_out["anomaly"] == 1][[x_col, y_col]].dropna().values.tolist()
        if x_col and y_col else []
    )

    return jsonable_encoder({
        "summary":  summary,
        "rows":     df_json_safe,
        "file_id":  file_id,
        "heatmap":  heatmap_points,
        "heatmap_columns": {"x": x_col, "y": y_col},
    })


@app.get("/download/{file_id}")
async def download(file_id: str, user: Dict = Depends(get_current_user)):
    if file_id not in ANOMALY_STORE:
        raise HTTPException(status_code=404, detail="File ID not found")

    tmp_path = DATA_DIR / f"anomalies_{file_id}.csv"
    ANOMALY_STORE[file_id].to_csv(tmp_path, index=False)
    return FileResponse(tmp_path, filename=tmp_path.name, media_type="text/csv")

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await get_current_user_optional_ws(websocket)
    await websocket.accept()
    try:
        while True:
            is_anomaly = random.random() < 0.1
            row = {
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "Port": random.randint(1000, 65000),
                "Bytes": random.randint(1000, 10000),
                "Packets": random.randint(1, 500),
                "anomaly": 1 if is_anomaly else 0,
                "anomaly_reason": "Simulated high traffic" if is_anomaly else "",
            }
            await websocket.send_json(row)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")

@app.post("/clicks")
async def track_click(data: Dict):
    CLICK_STORE.append(data)
    return {"status": "recorded"}

@app.get("/heatmap/clicks")
async def get_clicks():
    valid_clicks = [
        d for d in CLICK_STORE
        if isinstance(d, dict)
        and isinstance(d.get("x"), (int, float))
        and isinstance(d.get("y"), (int, float))
    ]
    return valid_clicks


@app.post("/path")
async def track_path(data: Dict):
    NAV_PATHS.append(data)
    return {"status": "path recorded"}

@app.get("/paths/flow")
async def get_path_flow():
    transitions = {}
    previous_path = None

    for entry in NAV_PATHS:
        current_path = entry.get("pathname")
        if previous_path is not None:
            key = (previous_path, current_path)
            transitions[key] = transitions.get(key, 0) + 1
        previous_path = current_path

    path_set = set()
    for (source, target) in transitions:
        path_set.add(source)
        path_set.add(target)

    node_list = list(path_set)
    node_index = {name: i for i, name in enumerate(node_list)}
    nodes = [{"name": name} for name in node_list]
    links = [
        {"source": node_index[source], "target": node_index[target], "value": count}
        for (source, target), count in transitions.items()
    ]

    return {"nodes": nodes, "links": links}   