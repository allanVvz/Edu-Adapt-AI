from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Column
from sqlalchemy import JSON
import uuid


class Activity(SQLModel, table=True):
    __tablename__ = "activities"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    teacher_id: str = Field(foreign_key="users.id")
    story_id: Optional[str] = Field(default=None, foreign_key="stories.id")
    title: str
    discipline: Optional[str] = None
    school_year: Optional[str] = None
    pedagogical_objective: Optional[str] = None
    bncc_skill: Optional[str] = None
    activity_type: Optional[str] = None  # multiple_choice, essay, association, drag_drop, game
    statement: Optional[str] = None
    question: Optional[str] = None
    expected_answer: Optional[str] = None
    correction_criteria: Optional[str] = None
    base_complexity: int = Field(default=2)
    original_modality: Optional[str] = None
    teacher_notes: Optional[str] = None
    status: str = Field(default="draft")  # draft, active, archived
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
