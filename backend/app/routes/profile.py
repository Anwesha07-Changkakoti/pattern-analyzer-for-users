from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from app.database import get_db
from app.models import UserBehaviorProfile, UserSession, UserActivityLog,ActivityLog
from app.utils.firebase_auth import get_current_user
from app.utils.session_tracker import start_session, end_session
from app.services.behavior_profile import extract_behavior_features_from_activity,extract_behavior_profiles_for_all_users
from app.services.profile_updater import upsert_behavior_profile
import datetime
from typing import List, Dict



profile_router = APIRouter(prefix="/api/profile", tags=["Behavior"])

@profile_router.post("/update-from-activity")
async def update_profile_from_activity(user=Depends(get_current_user), db: Session = Depends(get_db)):
    print(f"🔧 POST /api/profile/update-from-activity called for: {user['uid']}")


    # Step 1: Get logs
    logs = db.query(ActivityLog).filter(ActivityLog.user_id == user["uid"]).all()
    print(f"📊 Found {len(logs)} activity logs for user {user['uid']}")

    if not logs:
        raise HTTPException(404, "No activity found")

    # Step 2: Get session durations
    sessions = db.query(UserSession).filter(UserSession.user_id == user["uid"]).all()
    print(f"🕒 Found {len(sessions)} recorded sessions for user {user['uid']}")

    # Step 3: Extract behavior features
    features = extract_behavior_features_from_activity(db, logs, sessions, user["uid"])

    # Step 4: Upsert into profile table
    upsert_behavior_profile(db, features)

    return {"message": "Behavior profile updated from activity"}



@profile_router.get("/track")
def simulate_session(db: Session = Depends(get_db), user=Depends(get_current_user)):
    from datetime import datetime, timedelta

    start_time = datetime.utcnow()
    end_time = start_time + timedelta(seconds=2.5)
    duration = (end_time - start_time).total_seconds()

    db.execute(
        """
        INSERT INTO sessions (user_id, start_time, end_time, duration)
        VALUES (:user_id, :start_time, :end_time, :duration)
        """,
        {
            "user_id": user["uid"],
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration,
        }
    )
    db.commit()

    return {"message": "Session tracked"}



@profile_router.get("/")
def get_profile(user=Depends(get_current_user), db: Session = Depends(get_db)):
    print("✅ /profile endpoint called for:", user["uid"])

    all_profiles = db.query(UserBehaviorProfile).all()
    print("Stored user_ids:", [p.user_id for p in all_profiles])

    profile = db.query(UserBehaviorProfile).filter(
        func.trim(func.lower(UserBehaviorProfile.user_id)) == user["uid"].strip().lower()
    ).first()

    if not profile:
        print(f"❌ No profile found for user {user['uid']}")
        return {"message": "No activity logs found", "updated": False}
    return {
        "avg_login_hour": profile.avg_login_hour,
        "avg_files_accessed": profile.avg_files_accessed,
        "avg_session_duration": profile.avg_session_duration,
        "common_file_types": profile.common_file_types,
        "frequent_regions": profile.frequent_regions,
        "weekdays_active": profile.weekdays_active,
    }


@profile_router.get("/session-trend")
def get_session_trend(user=Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = user["uid"]
    query = text("""
        SELECT 
            strftime('%w', start_time) AS weekday,
            AVG(duration) as avg_duration
        FROM sessions
        WHERE user_id = :user_id
        GROUP BY weekday
        ORDER BY weekday
    """)
    result = db.execute(query, {"user_id": user_id}).fetchall()

    weekdays = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    trend = [
        {"day": weekdays[int(row[0])], "duration": round(row[1], 2)}
        for row in result
    ]
    return trend

@profile_router.get("/stats")
def get_behavior_stats(user=Depends(get_current_user), db: Session = Depends(get_db)):
    today = datetime.datetime.utcnow().date()

    logs = db.query(ActivityLog).filter(ActivityLog.user_id == user["uid"]).all()

    ip_addresses = list({log.ip_address for log in logs})

    # Session = any log where no file was uploaded
    session_count = len([log for log in logs if not log.file_uploaded])

    # Upload count for today
    upload_count_today = db.query(UserActivityLog).filter(
        UserActivityLog.user_id == user["uid"],
        UserActivityLog.file_uploaded == True,
        func.date(UserActivityLog.timestamp) == today
    ).count()

    # Total duration spent on site (all logs)
    total_duration = sum([0 if log.duration_seconds is None else log.duration_seconds for log in logs])

    # Detect anomalies
    anomalies = []
    if upload_count_today > 10:
        anomalies.append("🚨 Excessive file uploads today")

    # Optional: Detect off-hour usage (between 00:00–06:00)
    odd_hour_logs = [log for log in logs if 0 <= log.timestamp.hour <= 6]
    if len(odd_hour_logs) > 0:
        anomalies.append(f"⚠️ User active during odd hours ({len(odd_hour_logs)} times)")

    return {
        "user_id": user["uid"],
        "ip_addresses": ip_addresses,
        "session_count": session_count,
        "upload_count_today": upload_count_today,
        "total_duration_minutes": round(total_duration / 60, 2),
        "anomalies": anomalies,
        "daily_usage": get_daily_usage(user["uid"], db)
    }

@profile_router.get("/users/behavior-profiles")
def get_all_behavior_profiles(db: Session = Depends(get_db)):
    user_ids = db.query(ActivityLog.user_id).distinct().all()
    profiles = []

    logs = db.query(ActivityLog).all()
    sessions = db.query(UserSession).all()

    profiles = extract_behavior_profiles_for_all_users(db, logs, sessions)

    for profile in profiles:
       upsert_behavior_profile(db, profile)

    return profiles


def get_daily_usage(user_id: str, db: Session):
    data = db.query(
        func.date(UserActivityLog.timestamp).label("date"),
        func.sum(UserActivityLog.duration_seconds).label("duration")
    ).filter(
        UserActivityLog.user_id == user_id
    ).group_by(func.date(UserActivityLog.timestamp)).all()

    return [
        {"date": str(row.date), "duration_minutes": round(row.duration / 60, 2)}
        for row in data
    ]
@profile_router.get("/all-profiles", response_model=List[Dict])
def get_all_user_behavior_profiles(db: Session = Depends(get_db)):
    logs = db.query(ActivityLog).all()
    sessions = db.query(UserSession).all()
    profiles = extract_behavior_profiles_for_all_users(db, logs, sessions)
    return profiles