from sqlalchemy import (
    Boolean, Column, DateTime, Integer, LargeBinary, String, Text, UniqueConstraint, func
)
from app.core.database import JobsBase


class JobPosting(JobsBase):
    """A job collected by the ingestion pipeline. Search ranks these rows; it never scrapes live."""
    __tablename__ = "job_postings"
    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_job_source_external_id"),)

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(64), nullable=False, index=True)
    external_id = Column(String(255), nullable=False)
    dedupe_key = Column(String(512), nullable=False, index=True)
    content_hash = Column(String(64), nullable=False)

    title = Column(String(512), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(512), nullable=True)
    countries = Column(String(128), nullable=False)
    remote = Column(Boolean, nullable=False, default=False)
    seniority = Column(String(16), nullable=True)
    description = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    translated = Column(Boolean, nullable=False, default=False)

    skills = Column(Text, nullable=True)  
    embedding = Column(LargeBinary, nullable=True) 

    posted_at = Column(DateTime(timezone=True), nullable=True)
    first_seen_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class IngestionRun(JobsBase):
    __tablename__ = "ingestion_runs"

    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    heartbeat_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(16), nullable=False, default="running")
    stats = Column(Text, nullable=True)
