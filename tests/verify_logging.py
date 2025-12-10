import logging
import os
from app.core.logging_config import setup_logging

def test_logging_setup():
    # Force reset of logging handlers for test
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
        
    # Setup logging
    setup_logging(log_dir="tests/logs", log_file="test_log.txt")
    
    logger = logging.getLogger("test_logger")
    test_message = "This is a test log message."
    logger.info(test_message)
    
    # Check if file exists
    log_file = "tests/logs/test_log.txt"
    assert os.path.exists(log_file)
    
    # Check content
    with open(log_file, "r") as f:
        content = f.read()
        assert test_message in content
        assert "INFO" in content

if __name__ == "__main__":
    test_logging_setup()
    print("Logging verification passed!")
