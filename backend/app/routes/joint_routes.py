from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.joint_model import compute_joint_anomaly_score
from app.model.joint_risk_score import UserJointRiskScore
import numpy as np

router = APIRouter()

def convert_numpy_types(obj: dict):
    converted = {}
    for k, v in obj.items():
        if isinstance(v, (np.generic, np.bool_)):
            converted[k] = v.item()
        else:
            converted[k] = v
    return converted

@router.get("/api/joint_score/{user_id}")
def get_joint_score(user_id: str, db: Session = Depends(get_db)):
    result = compute_joint_anomaly_score(db, user_id)
    if result:
        result = convert_numpy_types(result)
        score = UserJointRiskScore(**result)
        db.add(score)
        db.commit()
        return result
    return {"error": "User not found or insufficient data"}
