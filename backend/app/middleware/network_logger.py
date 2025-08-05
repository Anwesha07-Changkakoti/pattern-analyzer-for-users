# app/middleware/network_logger.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.models import UserNetworkStats  # You must define this model
from app.database import SessionLocal
from datetime import datetime

class PerUserRequestSizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        user_id = "anonymous"
        try:
            auth_header = request.headers.get("authorization", "")
            token = auth_header.replace("Bearer ", "")
            if token:
                from app.utils.firebase_auth import verify_firebase_token
                decoded = await verify_firebase_token(token)
                if decoded:
                    user_id = decoded["uid"]
        except Exception as e:
            print("🔴 Token decode error in network logger:", e)

        req_body = await request.body()
        req_size = len(req_body)

        # Get the response
        response = await call_next(request)
        res_body = b"".join([chunk async for chunk in response.body_iterator])
        res_size = len(res_body)

        db = SessionLocal()
        try:
            record = UserNetworkStats(
                user_id=user_id,
                timestamp=datetime.utcnow(),
                request_bytes=req_size,
                response_bytes=res_size
            )
            db.add(record)
            db.commit()
        except Exception as e:
            print("🔴 Failed to log UserNetworkStats:", e)
        finally:
            db.close()

        return Response(content=res_body, status_code=response.status_code, headers=dict(response.headers))
