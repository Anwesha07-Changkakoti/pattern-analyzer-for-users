"""SQLAlchemy models for User Pattern Analyzer
Includes:
  • User                    – Firebase‑authenticated user
  • AnalysisResult          – per‑file anomaly analysis metadata
  • UserBehaviorProfile     – aggregated behaviour statistics used for behaviour‑based anomaly detection
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

# ---------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    uid   = Column(String, primary_key=True, index=True)   # Firebase UID
    email = Column(String, unique=True, index=True)
    role  = Column(String, default="user")

    # relationships
    results          = relationship("AnalysisResult",      back_populates="user", cascade="all, delete-orphan")
    behavior_profile = relationship("UserBehaviorProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

# ---------------------------------------------------------------------
# Per‑analysis file summary
# ---------------------------------------------------------------------
class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(String, ForeignKey("users.uid"))
    file_id       = Column(String, unique=True, index=True)  # UUID for CSV download
    file_name     = Column(String)
    total_records = Column(Integer)
    anomaly_count = Column(Integer)
    timestamp     = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="results")

# ---------------------------------------------------------------------
# Aggregated behaviour statistics (one row per user)
# ---------------------------------------------------------------------
class UserBehaviorProfile(Base):
    __tablename__ = "user_behavior_profiles"

    id                  = Column(Integer, primary_key=True, index=True)
    user_id             = Column(String, ForeignKey("users.uid"), unique=True)

    avg_login_hour      = Column(Float)   # 0‑23 mean login time
    avg_files_accessed  = Column(Float)   # daily mean
    common_file_types   = Column(String)  # comma‑separated e.g. "pdf,csv,docx"
    avg_session_duration= Column(Float)   # minutes
    frequent_regions    = Column(String)  # comma‑separated region codes/names
    weekdays_active     = Column(String)  # comma‑separated ints 0‑6 (Mon‑Sun)

    last_updated        = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="behavior_profile")
# ---------------------------------------------------------------------
# Per-session tracking (used for trend analysis)
# ---------------------------------------------------------------------
class Session(Base):
    __tablename__ = "sessions"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(String, ForeignKey("users.uid"))
    start_time = Column(DateTime)  # login timestamp
    duration   = Column(Float)     # session duration in seconds

    user = relationship("User")  # optional, if needed for joins
