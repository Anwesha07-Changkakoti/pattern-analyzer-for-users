from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.models import UserBehaviorProfile, Session as UserSession  # ✅ Add Session model
from app.utils.firebase_auth import get_current_user

router = APIRouter(prefix="/profile", tags=["Behavior"])


@router.get("/")
def get_profile(user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserBehaviorProfile).filter_by(user_id=user["uid"]).first()
    if not profile:
        raise HTTPException(404, "Profile not found")
    return {
        "avg_login_hour": profile.avg_login_hour,
        "avg_files_accessed": profile.avg_files_accessed,
        "avg_session_duration": profile.avg_session_duration,
        "common_file_types": profile.common_file_types,
        "frequent_regions": profile.frequent_regions,
        "weekdays_active": profile.weekdays_active,
    }


@router.get("/session-trend")
def get_session_trend(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns average session durations grouped by weekday
    for use in time-series charts.
    """
    user_id = user["uid"]

    # SQLite version (change for PostgreSQL accordingly)
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
