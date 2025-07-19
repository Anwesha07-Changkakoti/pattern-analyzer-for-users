from datetime import datetime
from app.models import UserSession


def store_session_data(db, user_id, session_id, timestamp, duration):
    try:
        start_time = datetime.fromisoformat(timestamp.replace("Z", ""))  # remove 'Z'
        session = SessionModel(
            user_id=user_id,
            session_id=session_id,
            start_time=start_time,
            duration=duration
        )
        db.add(session)
        db.commit()
    except Exception as e:
        print(f"[Session Save Error] {e}")
