from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.models import UserBehaviorProfile, UserSession
from app.utils.firebase_auth import get_current_user
from app.utils.session_tracker import start_session, end_session
import time

profile_router = APIRouter(prefix="/profile", tags=["Behavior"])

@profile_router.get("/track")
def simulate_session(db: Session = Depends(get_db), user=Depends(get_current_user)):
    session_data = start_session(user["uid"])
    time.sleep(2.5)
    end_session(db, session_data)
    return {"message": "Session tracked"}

@profile_router.get("/")
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
