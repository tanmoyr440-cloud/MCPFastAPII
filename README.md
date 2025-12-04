# AI Desk Chat Backend

FastAPI-based backend for AI Desk chat application with WebSocket support for real-time messaging and SQLite database for persistent storage.

Built with clean architecture principles separating models, API routes, and database configuration.

## Features

- REST API for session and message management
- WebSocket endpoint for real-time chat
- SQLite database with SQLModel ORM
- Persistent message and session storage
- CORS enabled for frontend communication
- Clean architecture with modular organization

## Project Structure

```
backend/
├── main.py                  # Entry point - starts the application
├── app/
│   ├── __init__.py         # Package initialization
│   ├── app.py              # FastAPI application factory
│   ├── schemas.py          # Pydantic request/response schemas
│   ├── models/
│   │   ├── __init__.py
│   │   ├── session.py      # ChatSession model
│   │   └── message.py      # Message model
│   ├── api/
│   │   ├── __init__.py
│   │   ├── sessions.py     # Session endpoints
│   │   └── websocket.py    # WebSocket handler
│   └── core/
│       ├── __init__.py
│       └── database.py     # Database configuration
├── pyproject.toml          # Dependencies
└── README.md               # This file
```

## Setup

```bash
# Install dependencies
pip install -e .

# Run the development server
python main.py
```

The API will be available at `http://localhost:8000`

- Interactive API docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Database

- **Database**: SQLite (`ai_desk.db`)
- **ORM**: SQLModel
- **Tables**:
  - `chatsession` - Stores chat session metadata
  - `message` - Stores individual messages linked to sessions

The database is automatically created on first startup.

## API Endpoints

### REST Endpoints

- `GET /` - Health check
- `GET /api/sessions` - Get all chat sessions with messages
- `POST /api/sessions` - Create a new session
- `GET /api/sessions/{session_id}` - Get session details with messages
- `POST /api/sessions/{session_id}/messages` - Add message to session

### WebSocket

- `WS /ws/{session_id}` - Real-time chat connection

## Message Format

### Request (REST POST)

```json
{
  "content": "Hello",
  "sender": "user",
  "timestamp": "2025-11-30T12:00:00.000Z"
}
```

### Response

```json
{
  "id": 1,
  "session_id": "123",
  "content": "Hello",
  "sender": "user",
  "timestamp": "2025-11-30T12:00:00.000Z"
}
```

### WebSocket Message

```json
{
  "session_id": "123",
  "message": {
    "id": 1,
    "content": "Hello",
    "sender": "user",
    "timestamp": "2025-11-30T12:00:00.000Z"
  }
}
```

## Data Models

### ChatSession

- `id` (string): Unique session identifier
- `title` (string): Session title
- `created_at` (string): ISO format timestamp

### Message

- `id` (integer): Auto-incrementing primary key
- `session_id` (string): Foreign key to ChatSession
- `content` (string): Message text
- `sender` (string): "user" or "assistant"
- `timestamp` (string): ISO format timestamp

```bash
# Install dependencies
pip install -e .

# Run the development server
python main.py
```

The API will be available at `http://localhost:8000`

- Interactive API docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### REST Endpoints

- `GET /` - Health check
- `GET /api/sessions` - Get all chat sessions
- `POST /api/sessions` - Create a new session
- `GET /api/sessions/{session_id}` - Get session details
- `POST /api/sessions/{session_id}/messages` - Add message to session

### WebSocket

- `WS /ws/{session_id}` - Real-time chat connection

## Message Format

```json
{
  "content": "Hello",
  "sender": "user",
  "timestamp": "2025-11-30T12:00:00"
}
```
