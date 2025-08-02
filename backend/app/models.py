"""SQLAlchemy models for User Pattern Analyzer.

Models:
    • User – Firebase-authenticated user.
    • AnalysisResult – Per-file anomaly analysis metadata.
    • UserBehaviorProfile – Aggregated behaviour stats for anomaly detection.
    • UserSession – Per-session activity tracking.
    • ActivityLog – Granular activity tracking.
    • UserActivityLog – Page-level behavior logging.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, ForeignKey, Index, func
)
from sqlalchemy.orm import relationship
from .database import Base


# ---------------------------------------------------------------------
# User
# ---------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    uid = Column(String, primary_key=True, index=True)  # Firebase UID
    email = Column(String, unique=True, index=True)
    role = Column(String, default="user")

    # Relationships
    results = relationship("AnalysisResult", back_populates="user", cascade="all, delete-orphan")
    behavior_profile = relationship("UserBehaviorProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")


# ---------------------------------------------------------------------
# Analysis Result
# ---------------------------------------------------------------------
class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"))
    file_id = Column(String, unique=True, index=True)  # UUID for CSV download
    file_name = Column(String)
    total_records = Column(Integer)
    anomaly_count = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="results")


# ---------------------------------------------------------------------
# User Behavior Profile
# ---------------------------------------------------------------------
class UserBehaviorProfile(Base):
    __tablename__ = "user_behavior_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), unique=True)

    avg_login_hour = Column(Float)
    avg_files_accessed = Column(Float)
    common_file_types = Column(String)
    avg_session_duration = Column(Float)
    frequent_regions = Column(String)
    weekdays_active = Column(String)

    total_sessions = Column(Integer, default=0)
    total_time_spent = Column(Float, default=0.0)
    total_uploads = Column(Integer, default=0)

    last_updated = Column(DateTime, default=datetime.utcnow)
    anomaly_score = Column(Float, default=0.0)

    user = relationship("User", back_populates="behavior_profile")


# ---------------------------------------------------------------------
# User Session
# ---------------------------------------------------------------------
class UserSession(Base):
    __tablename__ = "sessions"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    session_id = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    duration = Column(Float, nullable=False)

    user = relationship("User", back_populates="sessions")


# ---------------------------------------------------------------------
# Activity Log (Detailed actions)
# ---------------------------------------------------------------------
class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    device_id = Column(String, index=True)
    action_type = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    bytes_uploaded = Column(Integer, default=0)
    bytes_downloaded = Column(Integer, default=0)

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


# ---------------------------------------------------------------------
# User Activity Log (Page tracking)
# ---------------------------------------------------------------------
class UserActivityLog(Base):
    __tablename__ = "user_activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)  # Firebase UID or email
    ip_address = Column(String)
    bytes_uploaded = Column(Integer, default=0)
    bytes_downloaded = Column(Integer, default=0)
    page = Column(String)
    timestamp = Column(DateTime, default=func.now())
    duration_seconds = Column(Float, default=0.0)
    file_uploaded = Column(Boolean, default=False)

class UserNetworkStats(Base):
    __tablename__ = "user_network_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    ip_address = Column(String)
    location = Column(String)
    device_type = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class UserJointAnomaly(Base):
    __tablename__ = "user_joint_anomaly"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    behavior_score = Column(Float)
    network_score = Column(Float)
    joint_score = Column(Float)
    is_anomaly = Column(Boolean, default=False)
