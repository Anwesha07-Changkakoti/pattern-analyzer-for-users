from dotenv import load_dotenv
import os
load_dotenv()

firebase_key = os.getenv("FIREBASE_KEY")

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Depends,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
)
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder

import pandas as pd
import numpy as np
import uuid
import io
from pathlib import Path
from typing import Dict

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

# ──────────────────────────────────────────────
# Heat‑map helpers & constants
DAYS_ORDER = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def _find_timestamp_column(df: pd.DataFrame):
    """Return first column name that looks like a timestamp."""
    for col in df.columns:
        lower = col.lower()
        if "time" in lower or "date" in lower:
            return col
    return None


def _build_heatmap_matrix(df_anoms: pd.DataFrame, ts_col: str):
    """Return {day:[24 ints]} anomaly count matrix."""
    df_anoms[ts_col] = pd.to_datetime(df_anoms[ts_col], errors="coerce")
    df_anoms.dropna(subset=[ts_col], inplace=True)

    df_anoms["hour"] = df_anoms[ts_col].dt.hour
    df_anoms["day"] = df_anoms[ts_col].dt.day_name()

    matrix = {d: [0] * 24 for d in DAYS_ORDER}
    for _, row in df_anoms.iterrows():
        matrix[row["day"]][row["hour"]] += 1
    return matrix


# ──────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# Logging
logger = logging.getLogger("user‑pattern‑analyzer")
logging.basicConfig(level=logging.INFO)

# Local storage for CSV downloads
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

app = FastAPI(title="User Pattern Analyzer API")
print(">>> CORS MIDDLEWARE LOADED ✅ <<<")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://pattern-analyzer-for-users-gs2yele7t.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(results_router)


@app.get("/test-auth")
async def test_auth_route(user: Dict = Depends(get_current_user)):
    return {"message": "Authenticated!", "user": user}


ANOMALY_STORE: Dict[str, pd.DataFrame] = {}
LATEST_FILE_ID: str | None = None  # track most recent analysis


# ──────────────────────────────────────────────
# Upload + analysis
# ──────────────────────────────────────────────
@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    user: Dict = Depends(get_current_user),
):
    raw_bytes = await file.read()
    filename = file.filename or "uploaded"

    # 1) Parse
    try:
        if filename.endswith(".json"):
            df_raw = pd.read_json(io.BytesIO(raw_bytes))
        else:
            df_raw = pd.read_csv(io.BytesIO(raw_bytes))
    except Exception as exc:
        logger.exception("Failed to parse file")
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {exc}")

    # 2) Feature engineering
    df_proc = preprocess(df_raw)

    # 3) Detect anomalies
    preds, reasons = detect_anomalies(
        df_raw=df_proc,
        user_uid=user["uid"],
        file_name=filename,
        return_reasons=True,
    )

    # 4) Build response
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

    global LATEST_FILE_ID
    LATEST_FILE_ID = file_id

    df_json_safe = df_out.replace({np.nan: None}).to_dict(orient="records")

    return jsonable_encoder(
        {
            "summary": summary,
            "rows": df_json_safe,
            "file_id": file_id,
        }
    )


# ──────────────────────────────────────────────
# CSV download
# ──────────────────────────────────────────────
@app.get("/download/{file_id}")
async def download(
    file_id: str,
    user: Dict = Depends(get_current_user),
):
    if file_id not in ANOMALY_STORE:
        raise HTTPException(status_code=404, detail="File ID not found")

    tmp_path = DATA_DIR / f"anomalies_{file_id}.csv"
    ANOMALY_STORE[file_id].to_csv(tmp_path, index=False)

    return FileResponse(tmp_path, filename=tmp_path.name, media_type="text/csv")


# ──────────────────────────────────────────────
# Heat‑map analytics
# ──────────────────────────────────────────────
@app.get("/analytics/heatmap/{file_id}")
async def heatmap_for_file(file_id: str):
    if file_id not in ANOMALY_STORE:
        raise HTTPException(status_code=404, detail="File ID not found")

    df_anoms = ANOMALY_STORE[file_id].copy()
    ts_col = _find_timestamp_column(df_anoms)
    if ts_col is None:
        raise HTTPException(400, "No timestamp‑like column present")

    matrix = _build_heatmap_matrix(df_anoms, ts_col)
    return {"labels": list(range(24)), "data": matrix}


@app.get("/analytics/heatmap")
async def heatmap_latest():
    if LATEST_FILE_ID is None:
        raise HTTPException(404, "No analysis has been run yet")
    return await heatmap_for_file(LATEST_FILE_ID)


# ──────────────────────────────────────────────
# WebSocket demo (unchanged)
# ──────────────────────────────────────────────
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
