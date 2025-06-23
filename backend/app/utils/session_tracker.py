from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Session as UserSession

# Store login time when user starts
def start_session(user_id: str):
    return {
        "user_id": user_id,
        "start_time": datetime.utcnow()
    }

# End session and store it
def end_session(db: Session, session_data: dict):
    end_time = datetime.utcnow()
    duration = (end_time - session_data["start_time"]).total_seconds()

    session = UserSession(
        user_id=session_data["user_id"],
        start_time=session_data["start_time"],
        duration=duration
    )
    db.add(session)
    db.commit()
