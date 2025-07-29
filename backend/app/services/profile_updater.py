from sqlalchemy.orm import Session
from collections import defaultdict, Counter
from app.services.behavior_profile import extract_behavior_profiles_for_all_users
from app.models import UserBehaviorProfile, UserSession,ActivityLog
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from typing import Dict,List


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
def generate_all_user_behavior_profiles(db: Session) -> List[dict]:
    logs = db.query(ActivityLog).all()
    sessions = db.query(UserSession).all()

    profiles_with_scores = extract_behavior_profiles_for_all_users(db, logs, sessions)
    score_map = {p["user_id"]: p.get("anomaly_score", None) for p in profiles_with_scores}

    user_profiles = defaultdict(lambda: {
        "user_id": "",
        "active_weekdays": set(),
        "time_spent_per_day": defaultdict(float),
        "ip_addresses": set(),
        "uploads_per_day": defaultdict(int),
        "login_hours": [],
        "known_devices": set(),  # inferred from user agent / ip
        "tags": set()
    })

    # Thresholds for anomaly tags
    UPLOAD_THRESHOLD = 5
    LATE_HOUR = 20  # After 8 PM
    LONG_SESSION_MINUTES = 60

    for log in logs:
        user_id = log.user_id
        profile = user_profiles[user_id]
        profile["user_id"] = user_id

        if log.timestamp:
            weekday = log.timestamp.strftime("%A")
            profile["active_weekdays"].add(weekday)
            profile["login_hours"].append(log.timestamp.hour)
            if log.timestamp.hour >= LATE_HOUR:
                profile["tags"].add("Late Login")

        if log.file_uploaded:
            day = log.timestamp.strftime("%Y-%m-%d")
            profile["uploads_per_day"][day] += 1

        if log.ip_address:
            if log.ip_address not in profile["ip_addresses"] and len(profile["ip_addresses"]) > 0:
                profile["tags"].add("New Device")
            profile["ip_addresses"].add(log.ip_address)

    for session in sessions:
        if session.start_time:
            day = session.start_time.strftime("%Y-%m-%d")
            duration = session.duration or 0
            profile = user_profiles[session.user_id]
            profile["time_spent_per_day"][day] += duration
            if duration >= LONG_SESSION_MINUTES:
                profile["tags"].add("Long Session")

    final_profiles = []
    for user_id, profile in user_profiles.items():
        uploads_sorted = dict(sorted(profile["uploads_per_day"].items()))
        time_sorted = dict(sorted(profile["time_spent_per_day"].items()))
        total_uploads = sum(uploads_sorted.values())

        # Add Unusual Upload Volume tag
        if any(v > UPLOAD_THRESHOLD for v in uploads_sorted.values()):
            profile["tags"].add("Unusual Upload Volume")

        final_profiles.append({
            "user_id": profile["user_id"],
            "active_weekdays": sorted(list(profile["active_weekdays"])),
            "ip_addresses": sorted(list(profile["ip_addresses"])),
            "uploads_per_day": uploads_sorted,
            "time_spent_per_day": time_sorted,
            "total_uploads": total_uploads,
            "total_time_minutes": round(sum(time_sorted.values()), 2),
            "anomaly_score": score_map.get(profile["user_id"], "N/A"),
            "tags": sorted(list(profile["tags"]))
        })

    return final_profiles
