from dotenv import load_dotenv
load_dotenv()
import os
import socketio
from socketio import ASGIApp

from fastapi.responses import JSONResponse
from fastapi import FastAPI, UploadFile, File, Depends, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from collections import defaultdict
from fastapi import Request
import pandas as pd
import numpy as np
import uuid
import io
from pathlib import Path
from typing import Dict, List

from sqlalchemy.orm import Session
from sqlalchemy import func

import logging
import asyncio
import datetime
import random


# App Services & DB
from app.services.ml_model import detect_anomalies
from app.services.feature_engineering import preprocess
from app.services.behavior_profile import extract_behavior_features_from_activity
from app.services.profile_updater import upsert_behavior_profile
from app.services.session_utils import store_session_data
from app.utils.session_tracker import start_session, end_session
from app.database import get_db, SessionLocal
from app.models import Base, AnalysisResult, ActivityLog
from app.schemas import ActivityLogCreate
from app.database import engine
from app.models import UserActivityLog



# Auth & Routes
from app.utils.firebase_auth import verify_firebase_token
from app.utils.firebase_auth import get_current_user, get_current_user_optional_ws
from app.routes.results import router as results_router
from app.routes.profile import profile_router
from app.routes.sessions import session_router
from pydantic import BaseModel
import inspect
from fastapi.routing import APIRoute

# Load env
print("FIREBASE_KEY found:", os.getenv("FIREBASE_KEY") is not None)
firebase_key = os.getenv("FIREBASE_KEY")

# Create FastAPI app FIRST
fastapi_app = FastAPI(title="User Pattern Analyzer API")

# Initialize socket.io server
sio = socketio.AsyncServer(
    cors_allowed_origins=[
        "https://pattern-analyzer-for-u-git-409984-anwesha-changkakotis-projects.vercel.app",
        "http://localhost:5173"
    ],
    async_mode="asgi"
)

# Wrap with Socket.IO ASGI App
app = ASGIApp(sio, other_asgi_app=fastapi_app)


@fastapi_app.options("/{full_path:path}")
async def preflight_handler(full_path: str, request: Request):
    response = JSONResponse(content={"message": "CORS preflight"})
    response.headers["Access-Control-Allow-Origin"] = request.headers.get("origin", "*")
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE"
    response.headers["Access-Control-Allow-Headers"] = request.headers.get(
        "Access-Control-Request-Headers", "*"
    )
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


@fastapi_app.middleware("http")
async def log_request_data(request: Request, call_next):
    start = datetime.datetime.utcnow()
    response = await call_next(request)
    duration = (datetime.datetime.utcnow() - start).total_seconds()

    user_id = "anonymous"
    try:
        auth_header = request.headers.get("authorization", "")
        token = auth_header.replace("Bearer ", "")
        if token:
            decoded = await verify_firebase_token(token)  # ✅ use await
            if decoded:
                user_id = decoded["uid"]
    except Exception as e:
        print("🔴 Failed to decode Firebase token:", e)

    try:
        db = next(get_db())
        ip = request.client.host
        log = UserActivityLog(
            ip_address=ip,
            page=request.url.path,
            duration_seconds=duration,
            user_id=user_id,
            timestamp=start,
            file_uploaded=False
        )
        db.add(log)
        db.commit()
    except Exception as e:
        print("🔴 Logging to UserActivityLog failed:", e)

    return response


# Middleware
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://pattern-analyzer-for-u-git-409984-anwesha-changkakotis-projects.vercel.app",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
fastapi_app.include_router(results_router)
fastapi_app.include_router(session_router)
fastapi_app.include_router(profile_router)


# Logging
logger = logging.getLogger("user-pattern-analyzer")
logging.basicConfig(level=logging.INFO)

# Local storage
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# In-memory stores
ANOMALY_STORE: Dict[str, pd.DataFrame] = {}
CLICK_STORE: List[Dict] = []
SESSION_STORE: List[Dict] = []
NAV_PATHS: List[Dict] = []

# Ensure tables are created
Base.metadata.create_all(bind=engine, checkfirst=True)

# Schemas
class ActivityInput(BaseModel):
    deviceId: str
    actionType: str
    pathname: str
    timestamp: float


@fastapi_app.post("/upload-click-logs")
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

    if not {"x", "y"}.issubset(df.columns):
        df = df.reset_index()
        df["x"] = df["Port"] if "Port" in df.columns else df["index"] * 10
        df["y"] = df["Bytes"] if "Bytes" in df.columns else df["index"] * 5

    df["x"] = df["x"].astype(float).clip(0, 1200)
    df["y"] = df["y"].astype(float).clip(0, 600)
    df["timestamp"] = pd.Timestamp.now().value // 1_000_000

    for _, row in df.iterrows():
        if pd.notna(row["x"]) and pd.notna(row["y"]):
            CLICK_STORE.append({
                "x": float(row["x"]),
                "y": float(row["y"]),
                "timestamp": int(row.get("timestamp", pd.Timestamp.now().value // 1_000_000)),
                "pathname": "/uploaded"
            })

    return {"status": "clicks extracted", "count": len(df)}


@fastapi_app.post("/activity")
async def track_activity(data: ActivityInput, db: Session = Depends(get_db)):
    log = ActivityLog(
        device_id=data.deviceId,
        action_type=data.actionType,
        pathname=data.pathname,
        timestamp=datetime.datetime.fromtimestamp(data.timestamp / 1000.0)
    )
    db.add(log)
    db.commit()
    return {"status": "Activity logged"}


@fastapi_app.post("/api/log")
def log_activity(
    log: ActivityLogCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # Convert timestamp string to datetime
    log_time = log.timestamp  # ✅ CORRECT: Already a datetime object


    # Check for recent similar log (same user, action, path)
    recent_window = log_time - datetime.timedelta(seconds=5)


    duplicate = db.query(ActivityLog).filter(
        ActivityLog.user_id == user["uid"],
        ActivityLog.action_type == log.action_type,
        ActivityLog.pathname == log.pathname,
        ActivityLog.timestamp >= recent_window
    ).first()

    if duplicate:
        return {"message": "Duplicate log skipped"}

    # Save new log
    entry = ActivityLog(
        user_id=user["uid"],
        device_id=log.device_id,
        action_type=log.action_type,
        timestamp=log.timestamp,
        pathname=log.pathname,
        details=log.details,
    )
    db.add(entry)
    db.commit()
    return {"message": "Log saved"}

@fastapi_app.get("/api/devices")
def get_devices(db: Session = Depends(get_db)):
    result = db.query(ActivityLog.device_id).distinct().all()
    return {"devices": [d[0] for d in result]}


@fastapi_app.get("/api/check/{device_id}")
def check_device_anomaly(device_id: str, db: Session = Depends(get_db)):
    now = datetime.datetime.utcnow()
    five_min_ago = now - datetime.timedelta(minutes=5)

    logs = db.query(ActivityLog).filter(
        ActivityLog.device_id == device_id,
        ActivityLog.timestamp >= five_min_ago
    ).all()

    if len(logs) > 100:
        return {"anomalous": True, "reason": "Too many actions in last 5 minutes"}

    login_attempts = [log for log in logs if "login" in log.action_type.lower()]
    if len(login_attempts) > 10:
        return {"anomalous": True, "reason": "Too many login attempts"}

    return {"anomalous": False, "reason": "Normal behavior"}


@fastapi_app.get("/test-auth")
async def test_auth_route(user: Dict = Depends(get_current_user)):
    return {"message": "Authenticated!", "user": user}

@fastapi_app.post("/analyze")
async def analyze(
    request: Request, 
    file: UploadFile = File(...),
    user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session_id = start_session(user["uid"])
    raw_bytes = await file.read()
    filename = file.filename or "uploaded"

    try:
        df_raw = pd.read_json(io.BytesIO(raw_bytes)) if filename.endswith(".json") else pd.read_csv(io.BytesIO(raw_bytes))
    except Exception as exc:
        logger.exception("Failed to parse file")
        raise HTTPException(400, f"Failed to parse file: {exc}")

    df_proc = preprocess(df_raw)
    preds, reasons = detect_anomalies(df_raw=df_raw, user_uid=user["uid"], file_name=filename, return_reasons=True)
    df_out = df_raw.copy()
    df_out["anomaly"] = preds
    df_out["anomaly_reason"] = reasons

    for _, row in df_out.iterrows():
        row.session_id = row.get("session_id")
        timestamp = row.get("timestamp")
        duration = float(row.get("duration", 0)) if row.get("duration") else 0
        if session_id and timestamp:
            store_session_data(db, user["uid"], session_id, timestamp, duration)

    summary = {
        "total": len(df_out),
        "anomalies": int((df_out["anomaly"] == 1).sum()),
        "normal": int((df_out["anomaly"] == 0).sum()),
    }

    file_id = str(uuid.uuid4())
    ANOMALY_STORE[file_id] = df_out[df_out["anomaly"] == 1].copy()

    db.add(AnalysisResult(
        user_id=user["uid"],
        file_id=file_id,
        file_name=filename,
        total_records=summary["total"],
        anomaly_count=summary["anomalies"],
        timestamp=datetime.datetime.utcnow(),
    ))

    # ✅ Log this upload in UserActivityLog
    try:
        db.add(UserActivityLog(
            user_id=user["uid"],
            ip_address=request.client.host if request.client else "unknown",
            page="/analyze",
            timestamp=datetime.datetime.utcnow(),
            file_uploaded=True,
            duration_seconds=0.0
        ))
    except Exception as e:
        logger.warning(f"Failed to log upload activity: {e}")

    db.commit()

    df_json_safe = df_out.replace({np.nan: None}).to_dict(orient="records")
    numeric_cols = df_out.select_dtypes(include="number").columns.tolist()
    x_col, y_col = numeric_cols[:2] if len(numeric_cols) >= 2 else (None, None)
    heatmap_points = df_out[df_out["anomaly"] == 1][[x_col, y_col]].dropna().values.tolist() if x_col and y_col else []

    try:
        end_session(db, session_id)
    except Exception as e:
        logger.warning(f"Failed to end session: {e}")

    return jsonable_encoder({
        "summary": summary,
        "rows": df_json_safe,
        "file_id": file_id,
        "heatmap": heatmap_points,
        "heatmap_columns": {"x": x_col, "y": y_col},
    })


@fastapi_app.get("/download/{file_id}")
async def download(file_id: str, user: Dict = Depends(get_current_user)):
    if file_id not in ANOMALY_STORE:
        raise HTTPException(status_code=404, detail="File ID not found")

    tmp_path = DATA_DIR / f"anomalies_{file_id}.csv"
    ANOMALY_STORE[file_id].to_csv(tmp_path, index=False)
    return FileResponse(tmp_path, filename=tmp_path.name, media_type="text/csv")

@fastapi_app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await get_current_user_optional_ws(websocket)
    await websocket.accept()

    client_ip = websocket.client.host
    last_sent_ids = set()

    try:
        while True:
            with SessionLocal() as db:  # <-- FIXED
                recent_logs = db.query(ActivityLog).order_by(
                    ActivityLog.timestamp.desc()
                ).limit(100).all()

                for log in reversed(recent_logs):
                    if log.id not in last_sent_ids:
                        await websocket.send_json({
                            "id": log.id,
                            "timestamp": log.timestamp.isoformat(),
                            "device_id": log.device_id,
                            "action_type": log.action_type,
                            "pathname": log.pathname,
                            "details": log.details,
                            "ip_address": client_ip,
                            "anomaly": log.anomaly,
                        })
                        last_sent_ids.add(log.id)

                # Optional: memory safety
                if len(last_sent_ids) > 1000:
                    last_sent_ids = set(list(last_sent_ids)[-500:])

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")


@fastapi_app.post("/clicks")
async def track_click(data: Dict):
    CLICK_STORE.append(data)
    return {"status": "recorded"}


@fastapi_app.get("/heatmap/clicks")
async def get_clicks():
    return [
        d for d in CLICK_STORE
        if isinstance(d, dict)
        and isinstance(d.get("x"), (int, float))
        and isinstance(d.get("y"), (int, float))
    ]


@fastapi_app.post("/path")
async def track_path(data: Dict):
    NAV_PATHS.append(data)
    return {"status": "path recorded"}


@fastapi_app.get("/paths/flow")
async def get_path_flow():
    transitions = {}
    previous_path = None

    for entry in NAV_PATHS:
        current_path = entry.get("pathname")
        if previous_path is not None:
            key = (previous_path, current_path)
            transitions[key] = transitions.get(key, 0) + 1
        previous_path = current_path

    path_set = {p for pair in transitions for p in pair}
    node_list = list(path_set)
    node_index = {name: i for i, name in enumerate(node_list)}

    return {
        "nodes": [{"name": name} for name in node_list],
        "links": [
            {"source": node_index[source], "target": node_index[target], "value": count}
            for (source, target), count in transitions.items()
        ]
    }
print("\n🔍 Registered routes:")
for route in fastapi_app.routes:
    if isinstance(route, APIRoute):
        methods = ','.join(route.methods)
        print(f"{methods:10} - {route.path} -> {inspect.getsource(route.endpoint).strip()[:100]}...")