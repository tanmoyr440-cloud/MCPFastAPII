import mimetypes
import logging

logger = logging.getLogger(__name__)

def apply_fix():
    # Force correct MIME types
    mimetypes.add_type("application/javascript", ".js")
    mimetypes.add_type("text/css", ".css")
    
    # Patch init to prevent overwriting
    original_init = mimetypes.init
    def patched_init(files=None):
        original_init(files)
        mimetypes.add_type("application/javascript", ".js")
        mimetypes.add_type("text/css", ".css")
    mimetypes.init = patched_init
    
    # Verify
    type, _ = mimetypes.guess_type("test.js")
    logger.info(f"MIME type fix applied. test.js -> {type}")

apply_fix()
