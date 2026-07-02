from datetime import datetime
from typing import Optional
import uuid
from sqlmodel import SQLModel, Field


class GalleryImage(SQLModel, table=True):
    __tablename__ = "gallery_images"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    image_url: str
    description: str
    source: str = Field(default="generated")  # "generated" | "uploaded"
    style: Optional[str] = Field(default=None)  # "line_art" | "cartoon_2d" | null
    prompt: Optional[str] = Field(default=None)
    activity_id: Optional[str] = Field(default=None, foreign_key="activities.id")
    adaptation_id: Optional[str] = Field(default=None, foreign_key="activity_adaptations.id")
    user_id: str = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
