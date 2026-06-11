from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Column
from sqlalchemy import JSON
import uuid


class AgentRun(SQLModel, table=True):
    __tablename__ = "agent_runs"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    adaptation_id: str = Field(foreign_key="activity_adaptations.id")
    agent_name: str
    status: str = Field(default="pending")  # pending, running, completed, failed
    input_data: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    output_data: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    model_used: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
