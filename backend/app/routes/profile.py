from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import UserBehaviorProfile
from app.utils.firebase_auth import get_current_user

router = APIRouter(prefix="/profile", tags=["Behavior"])

@router.get("")
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
