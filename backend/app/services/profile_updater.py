from sqlalchemy.orm import Session
from app.models import UserBehaviorProfile, UserSession
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from statistics import mean

def upsert_behavior_profile(db: Session, behavior_data: dict):
    try:
        user_id = behavior_data.get("user_id")
        if not user_id:
            raise ValueError("Missing user_id in behavior_data")

        session_records = behavior_data.pop("session_trend", [])
        durations = []
        login_hours = []
        weekdays = []

        if session_records:
            db.query(UserSession).filter_by(user_id=user_id).delete()
            for session in session_records:
                start_time = session["date"]
                duration = session["avg_duration"]
                dt = datetime.fromisoformat(start_time)

                durations.append(duration)
                login_hours.append(dt.hour)
                weekdays.append(dt.weekday())

                db.add(UserSession(
                    user_id=user_id,
                    start_time=start_time,
                    duration=duration,
                ))

        # Recalculate behavior features from sessions
        behavior_data["avg_session_duration"] = round(mean(durations), 2) if durations else 0
        behavior_data["avg_login_hour"] = round(mean(login_hours), 2) if login_hours else 0
        behavior_data["weekdays_active"] = ",".join(map(str, sorted(set(weekdays)))) if weekdays else ""

        # Now upsert profile
        profile = db.query(UserBehaviorProfile).filter_by(user_id=user_id).first()
        if profile:
            for key, value in behavior_data.items():
                setattr(profile, key, value)
        else:
            profile = UserBehaviorProfile(**behavior_data)
            db.add(profile)

        db.commit()

    except (SQLAlchemyError, ValueError) as e:
        db.rollback()
        print(f"[ERROR] Failed to upsert behavior profile: {e}")
        raise