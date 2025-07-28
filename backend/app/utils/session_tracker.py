# app/utils/session_tracker.py
import time
from datetime import datetime
from typing import Dict
from app.models import UserSession

# Temporary in-memory store (replace with Redis or DB for production)
active_sessions: Dict[str, Dict] = {}

def start_session(user_id: str) -> str:
    print(f"🔥 start_session() called for user: {user_id}")
    """
    Starts a session and stores it in active_sessions.
    Returns a session_id.
    """
    session_id = f"{user_id}-{int(time.time())}"
    active_sessions[session_id] = {
        "user_id": user_id,
        "start_time": datetime.utcnow(),
    }
    return session_id

def end_session(db, session_id: str) -> Dict:
    print(f"🔥 end_session() called for session_id: {session_id}")
    session = active_sessions.pop(session_id, None)
    if not session:
        raise ValueError("Session not found")

    end_time = datetime.utcnow()
    duration = (end_time - session["start_time"]).total_seconds()

    new_session = UserSession(
        user_id=session["user_id"],
        session_id=session_id,
        start_time=session["start_time"],
        duration=duration,
    )
    db.add(new_session)
    db.commit()

    return {"user_id": session["user_id"], "duration": duration}

def get_active_sessions():
    return active_sessions