# app/routes/sessions.py
# app/routes/sessions.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.firebase_auth import get_current_user
from app.utils.session_tracker import start_session, end_session

session_router = APIRouter(prefix="/session", tags=["Session"])

@session_router.post("/start")
def api_start_session(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Starts a session and returns a session_id to the frontend.
    """
    session_info = start_session(user["uid"])
    return {"session_id": session_info["session_id"], "start_time": session_info["start_time"]}


@session_router.post("/end")
def api_end_session(
    session_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Ends the session and writes it to the database.
    """
    try:
        result = end_session(db, session_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
