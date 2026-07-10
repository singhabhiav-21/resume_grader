from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.models.db import base


class Jobs(base):
    __tablename__ = "jobs"

    job_id = Column(String, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"),  nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
