"""Tests for request/response schemas."""
import pytest
from app.schemas import MessageRead, MessageCreate, ChatSessionRead
from datetime import datetime


def test_message_create_schema():
    """Test MessageCreate schema validation."""
    # Valid data
    msg = MessageCreate(
        content="Hello",
        sender="user",
    )
    assert msg.content == "Hello"
    assert msg.sender == "user"
    assert msg.timestamp is None


def test_message_create_with_timestamp():
    """Test MessageCreate with optional timestamp."""
    timestamp = datetime.now().isoformat()
    msg = MessageCreate(
        content="Hello",
        sender="user",
        timestamp=timestamp,
    )
    assert msg.timestamp == timestamp


def test_message_read_schema():
    """Test MessageRead schema."""
    msg = MessageRead(
        id=1,
        content="Hello",
        sender="user",
        timestamp=datetime.now().isoformat(),
    )
    assert msg.id == 1
    assert msg.content == "Hello"
    assert msg.sender == "user"


def test_chat_session_read_empty():
    """Test ChatSessionRead with no messages."""
    session = ChatSessionRead(
        id="test-id",
        title="Test Session",
        created_at=datetime.now().isoformat(),
    )
    assert session.id == "test-id"
    assert session.title == "Test Session"
    assert session.messages == []


def test_chat_session_read_with_messages():
    """Test ChatSessionRead with messages."""
    messages = [
        MessageRead(
            id=1,
            content="Hello",
            sender="user",
            timestamp=datetime.now().isoformat(),
        ),
        MessageRead(
            id=2,
            content="Hi",
            sender="assistant",
            timestamp=datetime.now().isoformat(),
        ),
    ]
    session = ChatSessionRead(
        id="test-id",
        title="Test Session",
        created_at=datetime.now().isoformat(),
        messages=messages,
    )
    assert len(session.messages) == 2
    assert session.messages[0].sender == "user"
    assert session.messages[1].sender == "assistant"


def test_schemas_serialization():
    """Test schema serialization to dict."""
    msg = MessageRead(
        id=1,
        content="Test",
        sender="user",
        timestamp="2025-01-01T00:00:00",
    )
    msg_dict = msg.model_dump()
    assert msg_dict["id"] == 1
    assert msg_dict["content"] == "Test"
    assert msg_dict["sender"] == "user"
