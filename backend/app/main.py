from dotenv import load_dotenv
import os

load_dotenv()
firebase_key = os.getenv("FIREBASE_KEY")

from fastapi import FastAPI, UploadFile, File, Depends, WebSocket, WebSocketDisconnect, HTTPException, Request
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

from app.models import Base
from app.database import engine
from app.routes.results import router as results_router

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
logger = logging.getLogger("user​-pattern​-analyzer")
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
print(">>> CORS MIDDLEWARE LOADED ✅ <<<")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://pattern-analyzer-for-u-git-409984-anwesha-changkakotis-projects.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(results_router)

@app.get("/test-auth")
async def test_auth_route(user: Dict = Depends(get_current_user)):
    return {"message": "Authenticated!", "user": user}

@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    user: Dict = Depends(get_current_user),
):
    raw_bytes = await file.read()
    filename = file.filename or "uploaded"

    try:
        if filename.endswith(".json"):
            df_raw = pd.read_json(io.BytesIO(raw_bytes))
        else:
            df_raw = pd.read_csv(io.BytesIO(raw_bytes))
    except Exception as exc:
        logger.exception("Failed to parse file")
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {exc}")

    df_proc = preprocess(df_raw)
    preds, reasons = detect_anomalies(
        df_raw=df_proc,
        user_uid=user["uid"],
        file_name=filename,
        return_reasons=True,
    )

    df_out = df_raw.copy()
    df_out["anomaly"] = preds
    df_out["anomaly_reason"] = reasons

    summary = {
        "total": int(len(df_out)),
        "anomalies": int((df_out["anomaly"] == 1).sum()),
        "normal": int((df_out["anomaly"] == 0).sum()),
    }

    file_id = str(uuid.uuid4())
    ANOMALY_STORE[file_id] = df_out[df_out["anomaly"] == 1].copy()
    df_json_safe = df_out.replace({np.nan: None}).to_dict(orient="records")

    return jsonable_encoder({"summary": summary, "rows": df_json_safe, "file_id": file_id})

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

# ➕ Click tracking for heatmap
@app.post("/clicks")
async def track_click(data: Dict):
    CLICK_STORE.append(data)
    return {"status": "recorded"}

@app.get("/heatmap/clicks")
async def get_clicks():
    return CLICK_STORE

# ➕ Session replay tracking
@app.post("/session")
async def store_session(data: Dict):
    SESSION_STORE.append(data)
    return {"status": "session saved"}

@app.get("/session/latest")
async def get_latest_session():
    if not SESSION_STORE:
        raise HTTPException(status_code=404, detail="No sessions found")
    return SESSION_STORE[-1]

# ➕ Path tracking
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
