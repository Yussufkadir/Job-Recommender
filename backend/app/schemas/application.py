from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime
from app.models.job_application import ApplicationStatus

class ApplicationCreate(BaseModel):
    job_title: str
    company: str
    job_url: Optional[HttpUrl] = None
    status: ApplicationStatus = ApplicationStatus.SAVED
    notes: Optional[str] = None

class ApplicationPatch(BaseModel):
    status: Optional[ApplicationStatus] = None
    notes: Optional[str] = None

class ApplicationOut(BaseModel):
    id: int
    user_id: int
    job_title: str
    company: str
    job_url: Optional[HttpUrl]
    status: ApplicationStatus
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
