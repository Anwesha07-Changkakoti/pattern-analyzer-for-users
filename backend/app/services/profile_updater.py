from sqlalchemy.orm import Session
from collections import defaultdict, Counter
from app.models import UserBehaviorProfile, UserSession,ActivityLog
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from typing import Dict


def upsert_behavior_profile(db: Session, behavior_data: dict):
    try:
        user_id = behavior_data.get("user_id")
        if not user_id:
            raise ValueError("Missing user_id in behavior_data")

        print("Upserting behavior profile for user:", user_id)

        # Extract and remove session_trend before upserting profile
        session_records = behavior_data.pop("session_trend", [])

        # Upsert or create behavior profile
        profile = db.query(UserBehaviorProfile).filter_by(user_id=user_id).first()
        if profile:
            for key, value in behavior_data.items():
                setattr(profile, key, value)
        else:
            profile = UserBehaviorProfile(**behavior_data)
            db.add(profile)

        # Replace session trend with new session records
        if session_records:
            db.query(UserSession).filter_by(user_id=user_id).delete()
            for session in session_records:
                try:
                    start_time = datetime.strptime(session["date"], "%Y-%m-%d")
                    db.add(UserSession(
                        user_id=user_id,
                        start_time=start_time,
                        duration=session["avg_duration"]
                    ))
                except Exception as e:
                    print(f"[Session Insert Error] {e}")

        db.commit()
    except (SQLAlchemyError, ValueError) as e:
        db.rollback()
        print(f"[ERROR] Failed to upsert behavior profile: {e}")
        raise

def generate_all_user_behavior_profiles(db: Session) -> Dict:
    logs = db.query(ActivityLog).all()
    sessions = db.query(UserSession).all()

    # Dictionary: user_id -> behavior profile
    user_profiles = defaultdict(lambda: {
        "user_id": "",
        "active_weekdays": set(),
        "time_spent_per_day": defaultdict(float),
        "ip_addresses": set(),
        "uploads_per_day": defaultdict(int)
    })

    for log in logs:
        user_id = log.user_id
        profile = user_profiles[user_id]
        profile["user_id"] = user_id

        if log.timestamp:
            weekday = log.timestamp.strftime("%A")
            profile["active_weekdays"].add(weekday)

        if log.ip_address:
            profile["ip_addresses"].add(log.ip_address)

        if log.action_type == "upload" and log.timestamp:
            day = log.timestamp.strftime("%Y-%m-%d")
            profile["uploads_per_day"][day] += 1

    for session in sessions:
        if session.start_time:
            day = session.start_time.strftime("%Y-%m-%d")
            user_profiles[session.user_id]["time_spent_per_day"][day] += session.duration

    # Convert sets to lists and defaultdicts to dicts
    for user_id, profile in user_profiles.items():
        profile["active_weekdays"] = list(profile["active_weekdays"])
        profile["ip_addresses"] = list(profile["ip_addresses"])
        profile["uploads_per_day"] = dict(profile["uploads_per_day"])
        profile["time_spent_per_day"] = dict(profile["time_spent_per_day"])

    return list(user_profiles.values())
