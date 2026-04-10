from enum import Enum as PyEnum
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class ApplicationStatus(str, PyEnum):
    SAVED = "saved",
    APPLIED = "applied",
    INTERVIEW = "interview",
    OFFER = "offer",
    REJECTED = "rejected"

class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    job_title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    job_url = Column(String(255), nullable=True)
    status = Column(Enum(ApplicationStatus), nullable=False, default=ApplicationStatus.SAVED)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)