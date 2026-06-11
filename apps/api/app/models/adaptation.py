from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Column
from sqlalchemy import JSON
import uuid


class ActivityAdaptation(SQLModel, table=True):
    __tablename__ = "activity_adaptations"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    activity_id: str = Field(foreign_key="activities.id")
    student_profile_id: Optional[str] = Field(default=None, foreign_key="student_profiles.id")
    student_id: Optional[str] = Field(default=None, foreign_key="students.id")
    generated_by: str = Field(default="mock")  # mock, openai
    output_data: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    status: str = Field(default="draft")  # draft, review, approved, rejected, published
    validator_feedback: Optional[str] = None
    teacher_feedback: Optional[str] = None
    version: int = Field(default=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
