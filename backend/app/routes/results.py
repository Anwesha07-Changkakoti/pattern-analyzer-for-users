"""app/routes/results.py
Routes for listing past analysis runs and downloading their anomaly CSVs.
All rows are scoped per‑user (Firebase uid).
"""
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AnalysisResult
from app.utils.firebase_auth import get_current_user

router = APIRouter(prefix="/results", tags=["History"])

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------
# 1️⃣  List past results (optionally filtered)
# ---------------------------------------------------------------------
@router.get("/history", response_model=List[Dict])
def get_past_results(
    start_date: Optional[str] = Query(None, description="DD-MM-YYYY"),
    end_date:   Optional[str] = Query(None, description="DD-MM-YYYY"),
    filename:   Optional[str] = Query(None, description="Partial or full file name"),
    db: Session = Depends(get_db),
    user       = Depends(get_current_user),
):
    """Return all AnalysisResult rows for the current user.
    Accept optional *inclusive* date range and filename substring filters.
    """
    query = db.query(AnalysisResult).filter(AnalysisResult.user_id == user["uid"])

    # filename filter (ILIKE for case‑insensitive search)
    if filename:
        query = query.filter(AnalysisResult.file_name.ilike(f"%{filename}%"))

    fmt = "%d-%m-%Y"  # expected incoming format
    try:
        if start_date:
            start_dt = datetime.strptime(start_date, fmt)
            query = query.filter(AnalysisResult.timestamp >= start_dt)
        if end_date:
            end_dt = datetime.strptime(end_date, fmt) + timedelta(days=1)
            query = query.filter(AnalysisResult.timestamp < end_dt)
    except ValueError:
        raise HTTPException(400, "Dates must be DD-MM-YYYY")

    rows = query.order_by(AnalysisResult.timestamp.desc()).all()

    return [
        {
            "file_id":       r.file_id,
            "file_name":     r.file_name,
            "timestamp":     r.timestamp.strftime("%d/%m/%Y, %H:%M:%S"),
            "total_records": r.total_records,
            "anomaly_count": r.anomaly_count,
        }
        for r in rows
    ]

# ---------------------------------------------------------------------
# 2️⃣  Download anomaly CSV by file_id
# ---------------------------------------------------------------------
@router.get("/download/{file_id}")
def download_csv(
    file_id: str,
    db: Session = Depends(get_db),
    user      = Depends(get_current_user),
):
    """Download the anomaly CSV that was generated for a given analysis run."""
    row = (
        db.query(AnalysisResult)
        .filter(
            AnalysisResult.user_id == user["uid"],
            AnalysisResult.file_id == file_id,
        )
        .first()
    )
    if not row:
        raise HTTPException(404, "Result not found for user")

    csv_path = DATA_DIR / f"anomalies_{file_id}.csv"
    if not csv_path.exists():
        raise HTTPException(404, "CSV not found on server")

    return FileResponse(csv_path, filename=row.file_name, media_type="text/csv")
