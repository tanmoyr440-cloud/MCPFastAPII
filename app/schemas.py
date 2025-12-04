"""Pydantic schemas for API request/response."""
from sqlmodel import SQLModel, Field
from typing import Optional, List


class MessageRead(SQLModel):
    """Message response model"""

    id: Optional[int] = None
    content: str
    sender: str
    timestamp: str
    file_url: Optional[str] = None
    file_name: Optional[str] = None


class MessageCreate(SQLModel):
    """Message creation model"""

    content: str
    sender: str
    timestamp: Optional[str] = None
    file_url: Optional[str] = None
    file_name: Optional[str] = None


class ChatSessionRead(SQLModel):
    """Chat session response model"""

    id: str
    title: str
    created_at: str
    messages: List[MessageRead] = []


# Authentication Schemas


class UserRegister(SQLModel):
    """User registration request"""

    username: str = Field(min_length=3, max_length=50, description="Username")
    email: str = Field(description="Email address")
    firstname: str = Field(min_length=1, max_length=100, description="First Name")
    lastname: str = Field(min_length=1, max_length=100, description="Last Name")
    password: str = Field(min_length=8, description="Password (min 8 characters)")
    user_role: Optional[str] = Field(default="user", description="User Role")


class UserLogin(SQLModel):
    """User login request"""

    username: str = Field(description="Username")
    password: str = Field(description="Password")



class UserUpdate(SQLModel):
    """User update request"""

    firstname: Optional[str] = Field(default=None, min_length=1, max_length=100, description="First Name")
    lastname: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Last Name")
    email: Optional[str] = Field(default=None, description="Email address")
    password: Optional[str] = Field(default=None, min_length=8, description="Password (min 8 characters)")
    user_role: Optional[str] = Field(default=None, description="User Role")
    is_active: Optional[bool] = Field(default=None, description="Is Active")
    locked: Optional[bool] = Field(default=None, description="Is Locked")


class UserRead(SQLModel):
    """User response model (without password)"""

    id: Optional[int] = None
    username: str
    email: str
    firstname: str
    lastname: str
    user_role: str
    created_at: str
    is_active: bool = True
    locked: bool = False
    failed_login_attempts: int = 0


class UserWrapperResponse(SQLModel):
    """Wrapped user response"""
    user: UserRead


class TokenResponse(SQLModel):
    """JWT token response"""

    access_token: str
    token_type: str = "bearer"
    user: UserRead