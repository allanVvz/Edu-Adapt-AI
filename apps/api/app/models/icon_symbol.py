from datetime import datetime
from typing import Optional
import uuid
from sqlmodel import SQLModel, Field


class IconSymbol(SQLModel, table=True):
    __tablename__ = "icon_symbols"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    term: str = Field(index=True)
    normalized_term: str = Field(index=True)
    symbol: str
    symbol_type: str = Field(default="emoji")  # "emoji" | "pictogram" | "symbol"
    aliases: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
