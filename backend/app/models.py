"""SQLAlchemy models for User Pattern Analyzer
Includes:
  • User                    – Firebase‑authenticated user
  • AnalysisResult          – per‑file anomaly analysis metadata
  • UserBehaviorProfile     – aggregated behaviour statistics used for behaviour‑based anomaly detection
  • UserSession             – per-session activity tracking
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey,Boolean,func,Index
from sqlalchemy.orm import relationship, declarative_base
from .database import Base


# ---------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    uid   = Column(String, primary_key=True, index=True)   # Firebase UID
    email = Column(String, unique=True, index=True)
    role  = Column(String, default="user")

    # relationships
    results           = relationship("AnalysisResult",      back_populates="user", cascade="all, delete-orphan")
    behavior_profile  = relationship("UserBehaviorProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    sessions          = relationship("UserSession",         back_populates="user", cascade="all, delete-orphan")


# ---------------------------------------------------------------------
# Per‑analysis file summary
# ---------------------------------------------------------------------
class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id             = Column(Integer, primary_key=True, index=True)
    user_id        = Column(String, ForeignKey("users.uid"))
    file_id        = Column(String, unique=True, index=True)  # UUID for CSV download
    file_name      = Column(String)
    total_records  = Column(Integer)
    anomaly_count  = Column(Integer)
    timestamp      = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="results")


# ---------------------------------------------------------------------
# Aggregated behaviour statistics (one row per user)
# ---------------------------------------------------------------------
class UserBehaviorProfile(Base):
    __tablename__ = "user_behavior_profiles"

    id                   = Column(Integer, primary_key=True, index=True)
    user_id              = Column(String, ForeignKey("users.uid"), unique=True)

    avg_login_hour       = Column(Float)
    avg_files_accessed   = Column(Float)
    common_file_types    = Column(String)
    avg_session_duration = Column(Float)
    frequent_regions     = Column(String)
    weekdays_active      = Column(String)

    total_sessions       = Column(Integer, default=0)
    total_time_spent     = Column(Float, default=0.0)

    last_updated         = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="behavior_profile")


# ---------------------------------------------------------------------
# Per-session tracking (used for trend analysis)
# ---------------------------------------------------------------------
class UserSession(Base):
    __tablename__ = "sessions"
    __table_args__ = {"extend_existing": True}

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(String, ForeignKey("users.uid"), nullable=False)
    session_id  = Column(String, nullable=False)
    start_time  = Column(DateTime, nullable=False)
    duration    = Column(Float, nullable=False)

    user = relationship("User", back_populates="sessions")

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    device_id = Column(String, index=True)
    action_type = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    pathname = Column(String, nullable=True)
    details = Column(String, nullable=True)
    anomaly = Column(Integer, default=0)
    file_type = Column(String, nullable=True)
    region = Column(String, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    ip_address = Column(String)
    file_uploaded = Column(Boolean, default=False)

    __table_args__ = (
        Index("idx_user_action_path_time", "user_id", "action_type", "pathname", "timestamp"),
    )

    

    
class UserActivityLog(Base):
    __tablename__ = "user_activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)  # can be email or uid
    ip_address = Column(String)
    page = Column(String)
    timestamp = Column(DateTime, default=func.now())
    duration_seconds = Column(Float, default=0.0)
    file_uploaded = Column(Boolean, default=False)
    
