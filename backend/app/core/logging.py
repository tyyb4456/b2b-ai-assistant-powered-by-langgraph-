"""
Logging configuration using Loguru
Provides structured logging with rotation and retention
"""
import sys
from loguru import logger
from app.core.config import settings


def setup_logging():
    """
    Configure loguru logger for the application
    """
    
    # Remove default logger
    logger.remove()
    
    # Console logging (stdout)
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )
    
    # File logging (with rotation)
    if settings.LOG_FILE:
        logger.add(
            settings.LOG_FILE,
            level=settings.LOG_LEVEL,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="100 MB",  # Rotate when file reaches 100MB
            retention="30 days",  # Keep logs for 30 days
            compression="zip",  # Compress rotated logs
            serialize=False,  # JSON format for production
        )
    
    logger.info(f"Logging configured: level={settings.LOG_LEVEL}, file={settings.LOG_FILE}")
    
    return logger


# Initialize logger when module is imported
setup_logging()