"""
Logging configuration
"""

import logging
import sys
import os
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
load_dotenv()


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance with file and console handlers.

    Args:
        name: Logger name (usually __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        # Create logs directory if it doesn't exist
        os.makedirs(os.getenv("LOG_DIRECTORY", "./logs"), exist_ok=True)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # File handler - separate log files for different levels
        log_filename = os.path.join(
            os.getenv("LOG_DIRECTORY", "./logs"),
            f"app_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler = logging.FileHandler(log_filename)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Error log file
        error_log_filename = os.path.join(
            os.getenv("LOG_DIRECTORY", "./logs"),
            f"error_{datetime.now().strftime('%Y%m%d')}.log"
        )
        error_handler = logging.FileHandler(error_log_filename)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        logger.addHandler(error_handler)

    if level:
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    else:
        logger.setLevel(getattr(logging, os.getenv("LOG_LEVEL", "INFO"), logging.INFO))

    return logger
