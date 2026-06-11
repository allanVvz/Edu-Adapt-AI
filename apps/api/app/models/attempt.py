from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Column
from sqlalchemy import JSON
import uuid


class StudentActivityAttempt(SQLModel, table=True):
    __tablename__ = "student_activity_attempts"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    student_id: str = Field(foreign_key="students.id")
    activity_id: str = Field(foreign_key="activities.id")
    adaptation_id: str = Field(foreign_key="activity_adaptations.id")
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    status: str = Field(default="started")  # started, completed, abandoned
    raw_response: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    score: Optional[float] = None
    max_score: Optional[float] = None
    completion_time_seconds: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
