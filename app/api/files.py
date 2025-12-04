"""File upload API endpoints."""
import os
import uuid
from fastapi import APIRouter, UploadFile, File, Depends
from app.core import get_session

router = APIRouter(prefix="/api/files", tags=["files"])

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), session=Depends(get_session)):
    """Upload a file and return the file URL and name"""
    
    # Validate file
    if not file.filename:
        return {"error": "No file provided"}
    
    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Save file
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Return file info
    return {
        "file_url": f"/{UPLOAD_DIR}/{unique_filename}",
        "file_name": file.filename,
    }
