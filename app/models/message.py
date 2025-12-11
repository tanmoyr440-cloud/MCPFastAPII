"""Message model."""
from sqlmodel import SQLModel, Field
from sqlalchemy import JSON, Column
from typing import Optional, Dict
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
    
    # Sustainability Metrics
    token_count: Optional[int] = Field(default=None, description="Total tokens used")
    cost: Optional[float] = Field(default=None, description="Estimated cost in USD")
    carbon_footprint: Optional[float] = Field(default=None, description="Estimated carbon footprint in kg CO2e")
    
    # Evaluation Metrics
    evaluation_scores: Optional[Dict] = Field(default=None, sa_column=Column(JSON))
    is_flagged: bool = Field(default=False, description="Flagged if quality checks fail")
