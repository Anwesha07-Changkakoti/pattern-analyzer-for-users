from sqlalchemy.orm import Session
from app.models import UserBehaviorProfile

def upsert_behavior_profile(db: Session, behavior_data: dict):
    profile = db.query(UserBehaviorProfile).filter_by(user_id=behavior_data["user_id"]).first()
    if profile:
        for k, v in behavior_data.items():
            setattr(profile, k, v)
    else:
        profile = UserBehaviorProfile(**behavior_data)
        db.add(profile)
    db.commit()
