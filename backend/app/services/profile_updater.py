from sqlalchemy.orm import Session
from app.models import UserBehaviorProfile

def upsert_behavior_profile(db: Session, behavior_data: dict):
    print("Upserting behavior profile:", behavior_data)

    # Extract and remove session data if provided
    session_records = behavior_data.pop("session_trend", [])

    # Upsert profile summary
    profile = db.query(UserBehaviorProfile).filter_by(user_id=behavior_data["user_id"]).first()
    if profile:
        for k, v in behavior_data.items():
            setattr(profile, k, v)
    else:
        profile = UserBehaviorProfile(**behavior_data)
        db.add(profile)

    # Insert session trend records if provided
    for session in session_records:
        new_session = UserSession(
            user_id=behavior_data["user_id"],
            start_time=session["date"],
            duration=session["avg_duration"]
        )
        db.add(new_session)

    db.commit()
