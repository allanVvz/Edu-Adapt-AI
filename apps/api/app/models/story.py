from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Column
from sqlalchemy import JSON
import uuid


class Story(SQLModel, table=True):
    __tablename__ = "stories"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    teacher_id: str = Field(foreign_key="users.id")
    title: str
    content: str
    audio_options: Optional[list] = Field(default=None, sa_column=Column(JSON))
    image_options: Optional[list] = Field(default=None, sa_column=Column(JSON))
    status: str = Field(default="active")  # active, archived
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
