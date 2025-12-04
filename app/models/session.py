"""Chat session model."""
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class ChatSession(SQLModel, table=True):
    """Chat session database model"""

    id: str = Field(primary_key=True)
    title: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
