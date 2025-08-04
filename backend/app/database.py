import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# --- Detect environment-based database ---
DATABASE_URL = os.getenv("DATABASE_URL")  # This will be set on Render

if DATABASE_URL:
    # ✅ Running on Render or env variable is set
    SQLALCHEMY_DATABASE_URL = DATABASE_URL

    # If URL starts with "postgres://" (Render default), SQLAlchemy needs "postgresql://"
    if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

    engine = create_engine(SQLALCHEMY_DATABASE_URL)
else:
    # ✅ Local development with SQLite fallback
    SQLALCHEMY_DATABASE_URL = "sqlite:///./analyzer_v2.db"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
