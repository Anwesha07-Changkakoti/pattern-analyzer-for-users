# app/routes/sessions.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from uuid import uuid4
from datetime import datetime
import json
import pathlib

router = APIRouter(prefix="/session", tags=["session-replay"])

DATA_DIR = pathlib.Path(__file__).parent.parent / "data" / "sessions"
DATA_DIR.mkdir(parents=True, exist_ok=True)

class Session(BaseModel):
    id: str
    created_at: datetime
    events: List[Dict]

SESSION_CACHE: Dict[str, Session] = {}

def _save_to_disk(session: Session):
    with open(DATA_DIR / f"{session.id}.json", "w") as f:
        json.dump(session.dict(), f, default=str)

def _load_from_disk(session_id: str) -> Session | None:
    f = DATA_DIR / f"{session_id}.json"
    if f.exists():
        return Session.parse_file(f)
    return None

@router.post("/")
async def store_session(payload: Dict):
    if "events" not in payload or not isinstance(payload["events"], list):
        raise HTTPException(status_code=400, detail="`events` (list) required")

    session = Session(id=str(uuid4()), created_at=datetime.utcnow(), events=payload["events"])
    SESSION_CACHE[session.id] = session
    _save_to_disk(session)
    return {"status": "session saved", "id": session.id}

@router.get("/latest")
async def get_latest_session():
    if not SESSION_CACHE:
        for p in DATA_DIR.glob("*.json"):
            s = Session.parse_file(p)
            SESSION_CACHE[s.id] = s

    if not SESSION_CACHE:
        raise HTTPException(status_code=404, detail="No sessions found")

    latest = max(SESSION_CACHE.values(), key=lambda s: s.created_at)
    return latest

@router.get("/{session_id}")
async def get_session(session_id: str):
    if session_id in SESSION_CACHE:
        return SESSION_CACHE[session_id]
    session = _load_from_disk(session_id)
    if session:
        SESSION_CACHE[session.id] = session
        return session
    raise HTTPException(status_code=404, detail="Session not found")

@router.get("/")
async def list_sessions():
    if not SESSION_CACHE:
        for p in DATA_DIR.glob("*.json"):
            s = Session.parse_file(p)
            SESSION_CACHE[s.id] = s
    return [{"id": s.id, "created_at": s.created_at} for s in sorted(SESSION_CACHE.values(), key=lambda s: s.created_at, reverse=True)]
