from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class FirmwareOut(BaseModel):
    id: int
    version: str
    filename: str
    size: int
    sha256: str
    signature_b64: str
    uploader: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True

class JobCreate(BaseModel):
    device_id: str
    firmware_version: Optional[str] = None
    firmware_id: Optional[int] = None

class JobOut(BaseModel):
    job_id: str
    device_id: str
    firmware_version: str
    state: str

class EventOut(BaseModel):
    ts: datetime
    device_id: str
    topic: str
    status: str
    job_id: Optional[str] = None
    payload: Optional[str] = None