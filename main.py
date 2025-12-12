import os
import sys

# Force UTF-8 encoding for stdout/stderr to handle emojis on Windows
if sys.platform == "win32":
    # Set environment variable to ensure subprocesses use UTF-8
    os.environ["PYTHONIOENCODING"] = "utf-8"

# Apply MIME type fix for Windows registry issues (Phoenix UI blank page)
import app.core.fix_mimetypes 

from app.app import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
