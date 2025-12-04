"""WebSocket endpoint for real-time chat."""
from fastapi import WebSocket, Depends
from sqlmodel import Session, select
from app.core import get_session
from app.models import ChatSession, Message
from app.services import get_ai_response
import json
from datetime import datetime
from typing import List

# Store active WebSocket connections
active_connections: List[WebSocket] = []


async def websocket_endpoint(websocket: WebSocket, session_id: str, session: Session = Depends(get_session)):
    """WebSocket endpoint for real-time chat"""
    # Verify session exists
    chat_session = session.get(ChatSession, session_id)
    if not chat_session:
        await websocket.close(code=1008, reason="Session not found")
        return

    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Create message object
            timestamp = message_data.get("timestamp") or datetime.now().isoformat()
            message = Message(
                session_id=session_id,
                content=message_data.get("content"),
                sender=message_data.get("sender", "user"),
                timestamp=timestamp,
            )

            # Store message in database
            session.add(message)
            session.commit()
            session.refresh(message)

            # Broadcast to all connected clients
            await broadcast_message(session_id, message)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)


async def broadcast_message(session_id: str, message: Message):
    """Broadcast message to all connected WebSocket clients"""
    for connection in active_connections:
        try:
            await connection.send_json(
                {
                    "session_id": session_id,
                    "message": {
                        "id": message.id,
                        "content": message.content,
                        "sender": message.sender,
                        "timestamp": message.timestamp,
                        "file_url": message.file_url,
                        "file_name": message.file_name,
                    },
                }
            )
        except Exception as e:
            print(f"Error broadcasting message: {e}")
