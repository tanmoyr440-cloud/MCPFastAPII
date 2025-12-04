"""User model for authentication."""
from sqlmodel import SQLModel, Field
from typing import Optional


class User(SQLModel, table=True):
    """User database model with authentication support"""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, min_length=3, max_length=50)
    email: str = Field(unique=True, index=True)
    firstname: str = Field(max_length=100)
    lastname: str = Field(max_length=100)
    hashed_password: str
    user_role: str = Field(default="user", max_length=50)
    created_at: str = Field(default="")
    is_active: bool = Field(default=True)
    locked: bool = Field(default=False)
    failed_login_attempts: int = Field(default=0)
