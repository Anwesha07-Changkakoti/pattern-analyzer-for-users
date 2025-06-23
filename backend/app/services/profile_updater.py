from sqlalchemy.orm import Session
from app.models import UserBehaviorProfile, UserSession
from sqlalchemy.exc import SQLAlchemyError


def upsert_behavior_profile(db: Session, behavior_data: dict):
    try:
        user_id = behavior_data.get("user_id")
        if not user_id:
            raise ValueError("Missing user_id in behavior_data")

        print("Upserting behavior profile:", behavior_data)

        # Extract session trend records (if any)
        session_records = behavior_data.pop("session_trend", [])

        # Upsert main profile
        profile = db.query(UserBehaviorProfile).filter_by(user_id=user_id).first()
        if profile:
            for key, value in behavior_data.items():
                setattr(profile, key, value)
        else:
            profile = UserBehaviorProfile(**behavior_data)
            db.add(profile)

        # Optional: clear old sessions for the user (prevent duplicates)
        if session_records:
            db.query(UserSession).filter_by(user_id=user_id).delete()

        # Insert new session records
        for session in session_records:
            if "date" in session and "avg_duration" in session:
                db.add(UserSession(
                    user_id=user_id,
                    start_time=session["date"],
                    duration=session["avg_duration"]
                ))

        db.commit()

    except (SQLAlchemyError, ValueError) as e:
        db.rollback()
        print(f"[ERROR] Failed to upsert behavior profile: {e}")
        raise
