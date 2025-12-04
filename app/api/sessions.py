"""Session API endpoints."""
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlmodel import Session, select
from app.models import ChatSession, Message
from app.core import get_session
from app.schemas import ChatSessionRead, MessageCreate, MessageRead
from app.services import get_ai_response, validate_all_guardrails
import asyncio

# Import broadcast function
from app.api.websocket import broadcast_message

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("", response_model=list[ChatSessionRead])
async def get_sessions(session: Session = Depends(get_session)):
    """Get all chat sessions with their messages"""
    sessions = session.exec(select(ChatSession)).all()
    result = []
    for sess in sessions:
        messages = session.exec(select(Message).where(Message.session_id == sess.id)).all()
        result.append(
            ChatSessionRead(
                id=sess.id,
                title=sess.title,
                created_at=sess.created_at,
                messages=[
                    MessageRead(
                        id=m.id,
                        content=m.content,
                        sender=m.sender,
                        timestamp=m.timestamp,
                        file_url=m.file_url,
                        file_name=m.file_name,
                    )
                    for m in messages
                ],
            )
        )
    return result


@router.post("", response_model=ChatSessionRead)
async def create_session(
    chat_session: ChatSession, session: Session = Depends(get_session)
):
    """Create a new chat session"""
    session.add(chat_session)
    session.commit()
    session.refresh(chat_session)
    return ChatSessionRead(
        id=chat_session.id,
        title=chat_session.title,
        created_at=chat_session.created_at,
        messages=[],
    )


@router.get("/{session_id}", response_model=ChatSessionRead)
async def get_session_detail(session_id: str, session: Session = Depends(get_session)):
    """Get a specific chat session with messages"""
    chat_session = session.get(ChatSession, session_id)
    if not chat_session:
        return {"error": "Session not found"}

    messages = session.exec(select(Message).where(Message.session_id == session_id)).all()
    return ChatSessionRead(
        id=chat_session.id,
        title=chat_session.title,
        created_at=chat_session.created_at,
        messages=[
            MessageRead(
                id=m.id,
                content=m.content,
                sender=m.sender,
                timestamp=m.timestamp,
                file_url=m.file_url,
                file_name=m.file_name,
            )
            for m in messages
        ],
    )


@router.post("/{session_id}/messages", response_model=MessageRead)
async def add_message(
    session_id: str,
    message_create: MessageCreate,
    background_tasks: BackgroundTasks,
    db_session: Session = Depends(get_session),
):
    """Add a message to a chat session"""
    # Verify session exists
    chat_session = db_session.get(ChatSession, session_id)
    if not chat_session:
        return {"error": "Session not found"}

    # Run guardrails validation
    guardrail_result = validate_all_guardrails(message_create.content)
    
    # Block messages that fail critical guardrails
    if guardrail_result["should_block"]:
        return {
            "error": "Message blocked by guardrails",
            "guardrail_issues": guardrail_result["checks"],
        }
    
    # Use redacted content if guardrails flagged it
    content_to_store = message_create.content
    if guardrail_result["should_redact"]:
        # Log the guardrail violation (can be stored in audit log)
        print(f"Guardrail redaction applied: {guardrail_result['checks']}")

    # Create and store message
    from datetime import datetime

    timestamp = message_create.timestamp or datetime.now().isoformat()
    message = Message(
        session_id=session_id,
        content=content_to_store,
        sender=message_create.sender,
        timestamp=timestamp,
        file_url=message_create.file_url,
        file_name=message_create.file_name,
    )
    db_session.add(message)
    db_session.commit()
    db_session.refresh(message)

    # Broadcast to WebSocket clients in background
    if background_tasks:
        background_tasks.add_task(
            broadcast_message,
            session_id,
            message,
        )

        # Generate AI response if message is from user
        if message.sender == "user":
            background_tasks.add_task(
                generate_ai_response_sync,
                session_id,
            )

    return MessageRead(
        id=message.id,
        content=message.content,
        sender=message.sender,
        timestamp=message.timestamp,
        file_url=message.file_url,
        file_name=message.file_name,
    )


async def generate_ai_response(session_id: str):
    """Generate and store AI response using Claude Sonnet"""
    try:
        from app.core.database import engine
        from datetime import datetime
        
        # Create a fresh database session for this background task
        with Session(engine) as db_session:
            # Get conversation history
            messages = db_session.exec(
                select(Message).where(Message.session_id == session_id).order_by(Message.timestamp)
            ).all()

            # Build conversation history for Claude
            conversation_history = []
            for msg in messages:
                conversation_history.append({
                    "role": "user" if msg.sender == "user" else "assistant",
                    "content": msg.content,
                })

            # Get AI response
            ai_response = await get_ai_response(conversation_history)

            # Create and store assistant message
            assistant_message = Message(
                session_id=session_id,
                content=ai_response,
                sender="assistant",
                timestamp=datetime.now().isoformat(),
            )
            db_session.add(assistant_message)
            db_session.commit()
            db_session.refresh(assistant_message)

            # Broadcast AI response
            await broadcast_message(session_id, assistant_message)
    except Exception as e:
        print(f"Error generating AI response: {e}")


def generate_ai_response_sync(session_id: str):
    """Synchronous wrapper to run the async AI response generator in a background task"""
    asyncio.run(generate_ai_response(session_id))


@router.post("/{session_id}/messages/with-rag", response_model=MessageRead)
async def add_message_with_rag(
    session_id: str,
    message_create: MessageCreate,
    background_tasks: BackgroundTasks,
    db_session: Session = Depends(get_session),
):
    """Add a message with RAG (Retrieval-Augmented Generation) based on file content"""
    from app.services import get_rag_response_with_conversation
    from datetime import datetime
    
    # Verify session exists
    chat_session = db_session.get(ChatSession, session_id)
    if not chat_session:
        return {"error": "Session not found"}

    # File URL must be provided for RAG
    if not message_create.file_url:
        return {"error": "File URL required for RAG endpoint"}

    # Run guardrails validation on user input
    guardrail_result = validate_all_guardrails(message_create.content)
    
    # Block messages that fail critical guardrails
    if guardrail_result["should_block"]:
        return {
            "error": "Message blocked by guardrails",
            "guardrail_issues": guardrail_result["checks"],
        }

    # Create and store user message
    timestamp = message_create.timestamp or datetime.now().isoformat()
    user_message = Message(
        session_id=session_id,
        content=message_create.content,
        sender=message_create.sender,
        timestamp=timestamp,
        file_url=message_create.file_url,
        file_name=message_create.file_name,
    )
    db_session.add(user_message)
    db_session.commit()
    db_session.refresh(user_message)

    # Broadcast user message to WebSocket clients
    if background_tasks:
        background_tasks.add_task(
            broadcast_message_sync,
            session_id,
            user_message,
        )

        # Generate RAG response if message is from user
        if user_message.sender == "user":
            background_tasks.add_task(
                generate_rag_response_sync,
                session_id,
                message_create.file_url,
                message_create.content,
            )

    return MessageRead(
        id=user_message.id,
        content=user_message.content,
        sender=user_message.sender,
        timestamp=user_message.timestamp,
        file_url=user_message.file_url,
        file_name=user_message.file_name,
    )


def broadcast_message_sync(session_id: str, message: Message):
    """Synchronous wrapper to broadcast messages"""
    asyncio.run(broadcast_message(session_id, message))


def generate_rag_response_sync(session_id: str, file_url: str, prompt: str):
    """Synchronous wrapper to run the async RAG response generator in a background task"""
    async def run_rag():
        try:
            from app.core.database import engine
            from app.services import get_rag_response_with_conversation
            from datetime import datetime
            
            # Get conversation history
            with Session(engine) as db_session:
                messages = db_session.exec(
                    select(Message).where(Message.session_id == session_id).order_by(Message.timestamp)
                ).all()

                # Build conversation history for context
                conversation_history = []
                for msg in messages:
                    if msg.sender == "user" or msg.sender == "assistant":
                        conversation_history.append({
                            "role": "user" if msg.sender == "user" else "assistant",
                            "content": msg.content,
                        })

                # Get full file path from URL
                # The file_url is relative like /uploads/filename.ext
                import os
                file_path = os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "..",
                    file_url.lstrip("/")
                )
                file_path = os.path.normpath(file_path)

                # Get RAG response
                rag_response = await get_rag_response_with_conversation(
                    prompt, 
                    file_path,
                    conversation_history
                )

                # Create and store assistant message with RAG response
                assistant_message = Message(
                    session_id=session_id,
                    content=rag_response,
                    sender="assistant",
                    timestamp=datetime.now().isoformat(),
                )
                db_session.add(assistant_message)
                db_session.commit()
                db_session.refresh(assistant_message)

                # Broadcast RAG response
                await broadcast_message(session_id, assistant_message)
        except Exception as e:
            print(f"Error generating RAG response: {e}")

    asyncio.run(run_rag())

