"""Chat session model."""
import uuid
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class ChatSession(SQLModel, table=True):
    """Chat session database model"""

    # Added default_factory to generate UUIDs automatically
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    title: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
