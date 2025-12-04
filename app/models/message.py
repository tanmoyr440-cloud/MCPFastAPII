"""Message model."""
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Message(SQLModel, table=True):
    """Chat message database model"""

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="chatsession.id")
    content: str
    sender: str  # 'user' or 'assistant'
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    file_url: Optional[str] = None
    file_name: Optional[str] = None
