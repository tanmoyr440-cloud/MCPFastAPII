import sys
import io

# Force UTF-8 encoding for stdout/stderr to handle emojis on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

"""Application factory and configuration."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.core import create_db_and_tables
from app.api import sessions_router
from app.api.websocket import websocket_endpoint
from app.api.auth import router as auth_router
from app.api.files import router as files_router
from app.api.users import router as users_router
from app.api.agents import router as agents_router
# Import User model to register it with SQLModel
from app.models.user import User  # noqa: F401
from app.core.logging_config import setup_logging
from app.core.observability_config import initialize_observability, shutdown_observability

# Setup logging before app creation
setup_logging()

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(title="AI Desk Chat API", version="0.1.0")

    # CORS middleware for frontend communication
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Startup event
    @app.on_event("startup")
    def on_startup():
        """Create database and tables on startup"""
        create_db_and_tables()
        initialize_observability()

    @app.on_event("shutdown")
    def on_shutdown():
        """Cleanup on shutdown"""
        shutdown_observability()

    # Health check endpoint
    @app.get("/")
    async def health_check():
        """Health check endpoint"""
        return {"status": "ok", "service": "AI Desk Chat API"}

    # Include routes
    app.include_router(sessions_router)
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(files_router)
    app.include_router(agents_router)

    # WebSocket endpoint
    app.add_api_websocket_route("/ws/{session_id}", websocket_endpoint)

    # Mount uploads directory as static files
    uploads_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

    return app

