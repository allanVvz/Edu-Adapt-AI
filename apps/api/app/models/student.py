from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel
import uuid


class Student(SQLModel, table=True):
    __tablename__ = "students"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    profile_id: Optional[str] = Field(default=None, foreign_key="student_profiles.id")
    school_year: Optional[str] = None
    learning_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TeacherStudent(SQLModel, table=True):
    __tablename__ = "teacher_students"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    teacher_id: str = Field(foreign_key="users.id")
    student_id: str = Field(foreign_key="students.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
