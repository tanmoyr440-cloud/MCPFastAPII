"""Tests for database models."""
import pytest
from sqlmodel import Session
from app.models import ChatSession, Message
from datetime import datetime
from uuid import uuid4


def test_create_chat_session(session: Session):
    """Test creating a chat session."""
    chat_session = ChatSession(id=str(uuid4()), title="Test Session")
    session.add(chat_session)
    session.commit()
    session.refresh(chat_session)

    assert chat_session.id is not None
    assert chat_session.title == "Test Session"
    assert chat_session.created_at is not None


def test_create_message(session: Session):
    """Test creating a message."""
    chat_session = ChatSession(id=str(uuid4()), title="Test Session")
    session.add(chat_session)
    session.commit()
    session.refresh(chat_session)

    message = Message(
        session_id=chat_session.id,
        content="Hello, World!",
        sender="user",
        timestamp=datetime.now().isoformat(),
    )
    session.add(message)
    session.commit()
    session.refresh(message)

    assert message.id is not None
    assert message.content == "Hello, World!"
    assert message.sender == "user"
    assert message.session_id == chat_session.id


def test_message_foreign_key(session: Session):
    """Test message foreign key relationship."""
    chat_session = ChatSession(id=str(uuid4()), title="Test Session")
    session.add(chat_session)
    session.commit()
    session.refresh(chat_session)

    message = Message(
        session_id=chat_session.id,
        content="Test",
        sender="user",
        timestamp=datetime.now().isoformat(),
    )
    session.add(message)
    session.commit()

    # Retrieve and verify
    retrieved_message = session.get(Message, message.id)
    assert retrieved_message.session_id == chat_session.id


def test_multiple_messages_per_session(session: Session):
    """Test multiple messages in a single session."""
    chat_session = ChatSession(id=str(uuid4()), title="Test Session")
    session.add(chat_session)
    session.commit()
    session.refresh(chat_session)

    # Create multiple messages
    for i in range(5):
        message = Message(
            session_id=chat_session.id,
            content=f"Message {i}",
            sender="user" if i % 2 == 0 else "assistant",
            timestamp=datetime.now().isoformat(),
        )
        session.add(message)

    session.commit()

    # Verify all messages are associated
    from sqlmodel import select
    messages = session.exec(
        select(Message).where(Message.session_id == chat_session.id)
    ).all()

    assert len(messages) == 5
    assert all(msg.session_id == chat_session.id for msg in messages)


def test_session_timestamp_auto_generated(session: Session):
    """Test that session created_at is auto-generated."""
    chat_session = ChatSession(id=str(uuid4()), title="Test Session")
    session.add(chat_session)
    session.commit()
    session.refresh(chat_session)

    assert chat_session.created_at is not None
    # Verify it's a valid ISO format timestamp
    from datetime import datetime as dt
    try:
        dt.fromisoformat(chat_session.created_at)
    except ValueError:
        pytest.fail("created_at is not a valid ISO format timestamp")
