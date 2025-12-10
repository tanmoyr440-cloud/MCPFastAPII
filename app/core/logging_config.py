import logging
import sys
from pathlib import Path

def setup_logging(log_dir: str = "logs", log_file: str = "logs.txt"):
    """
    Setup centralized logging configuration.
    Logs are written to a file and the console.
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    log_file_path = log_path / log_file

    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set levels for some noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured. Writing to {log_file_path}")
