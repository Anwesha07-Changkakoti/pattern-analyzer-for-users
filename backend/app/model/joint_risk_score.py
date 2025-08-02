# models/joint_risk_score.py
from sqlalchemy import Column, String, Float, Boolean, DateTime, Integer
from app.database import Base
from datetime import datetime

class UserJointRiskScore(Base):
    __tablename__ = "user_joint_risk_score"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    joint_anomaly_score = Column(Float)
    is_anomalous = Column(Boolean)
    timestamp = Column(DateTime, default=datetime.utcnow)
