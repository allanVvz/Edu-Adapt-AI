from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel
import uuid


class ApiKey(SQLModel, table=True):
    __tablename__ = "api_keys"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    provider: str  # openai, anthropic, vercel, mcp, ai_brain
    key_name: str
    # NOTE: stored as plain text in MVP — must be encrypted (AES-256) before production
    encrypted_value: str
    status: str = Field(default="active")  # active, inactive
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
