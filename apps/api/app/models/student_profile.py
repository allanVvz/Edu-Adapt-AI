from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Column
from sqlalchemy import JSON
import uuid


class StudentProfile(SQLModel, table=True):
    __tablename__ = "student_profiles"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    teacher_id: str = Field(foreign_key="users.id")
    name: str
    description: Optional[str] = None
    reading_level: Optional[str] = None  # initial, basic, intermediate, advanced
    autonomy_level: Optional[str] = None  # low, medium, high
    main_difficulties: Optional[list] = Field(default=None, sa_column=Column(JSON))
    recommended_strategies: Optional[list] = Field(default=None, sa_column=Column(JSON))
    preferred_modalities: Optional[list] = Field(default=None, sa_column=Column(JSON))
    resources_to_avoid: Optional[list] = Field(default=None, sa_column=Column(JSON))
    accessibility_complexity: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
