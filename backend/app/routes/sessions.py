# app/routes/sessions.py

from fastapi import APIRouter, Request, HTTPException, status
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

def _warm_cache():
    for p in DATA_DIR.glob("*.json"):
        s = Session.parse_file(p)
        SESSION_CACHE.setdefault(s.id, s)

@router.post("/", status_code=status.HTTP_201_CREATED)
async def store_session(req: Request):
    raw = await req.body()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    events = payload.get("events")
    if not isinstance(events, list):
        raise HTTPException(status_code=400, detail="`events` (list) required")

    has_full_snapshot = any(ev.get("type") == 2 for ev in events)
    if not has_full_snapshot:
        return {"status": "ignored", "reason": "no full snapshot"}

    session = Session(
        id=str(uuid4()),
        created_at=datetime.utcnow(),
        events=events,
    )
    SESSION_CACHE[session.id] = session
    _save_to_disk(session)
    return {"status": "session saved", "id": session.id, "events": len(events)}

@router.get("/", response_model=List[Dict])
async def list_sessions():
    if not SESSION_CACHE:
        _warm_cache()
    sessions = sorted(SESSION_CACHE.values(), key=lambda s: s.created_at, reverse=True)
    return [{"id": s.id, "created_at": s.created_at} for s in sessions]

@router.get("/latest", response_model=Session)
async def get_latest_session():
    if not SESSION_CACHE:
        _warm_cache()
    if not SESSION_CACHE:
        raise HTTPException(status_code=404, detail="No sessions found")
    return max(SESSION_CACHE.values(), key=lambda s: s.created_at)

@router.get("/{session_id}", response_model=Session)
async def get_session(session_id: str):
    if session_id in SESSION_CACHE:
        return SESSION_CACHE[session_id]
    session = _load_from_disk(session_id)
    if session:
        SESSION_CACHE[session.id] = session
        return session
    raise HTTPException(status_code=404, detail="Session not found")
