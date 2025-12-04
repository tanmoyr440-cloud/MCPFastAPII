"""AI Desk Chat Application - Entry point."""
from dotenv import load_dotenv
import uvicorn
from app import create_app

# Load environment variables from .env file
load_dotenv()

# Create FastAPI application
app = create_app()

if __name__ == "__main__":
    # Run the development server
    uvicorn.run(app, host="0.0.0.0", port=8000)

