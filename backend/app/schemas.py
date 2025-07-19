from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ActivityLogCreate(BaseModel):
    device_id: str = Field(..., alias="deviceId")
    action_type: str
    timestamp: datetime
    pathname: Optional[str] = None
    details: Optional[str] = None

    class Config:
        allow_population_by_field_name = True
