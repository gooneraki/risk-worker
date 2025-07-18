"""Logger service - centralized logging configuration"""
import os
import logging
from logging.handlers import RotatingFileHandler

from app.utils import get_required_env

log_level: str = get_required_env("LOG_LEVEL")
log_file: str = get_required_env("LOG_FILE")


def setup_logging():
    """Setup logging configuration with rotation"""
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Setup rotating file handler
    rotating_handler = RotatingFileHandler(
        log_file,
        maxBytes=1*1024*1024,
        backupCount=10,
        encoding='utf-8'
    )

    # Setup console handler
    console_handler = logging.StreamHandler()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[rotating_handler, console_handler],
        force=True
    )

    return logging.getLogger(__name__)


logger = setup_logging()
