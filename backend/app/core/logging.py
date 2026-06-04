"""Structured JSON logging configuration"""
import logging
import sys
from pathlib import Path
from typing import Any, Dict
from logging.handlers import TimedRotatingFileHandler
from pythonjsonlogger import jsonlogger

from app.core.config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional context"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Add custom fields to log record"""
        super().add_fields(log_record, record, message_dict)
        
        # Add standard fields
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['timestamp'] = self.formatTime(record, self.datefmt)
        
        # Add environment context
        log_record['environment'] = settings.APP_ENV
        log_record['service'] = settings.APP_NAME


def setup_logging() -> None:
    """Configure application logging with rotation and retention"""
    
    # Determine log format
    if settings.LOG_FORMAT == "json":
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(logger)s %(message)s'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler with rotation for request/response logs
    # Only add file handler if LOG_FILE_PATH is configured
    if hasattr(settings, 'LOG_FILE_PATH') and settings.LOG_FILE_PATH:
        log_dir = Path(settings.LOG_FILE_PATH).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # TimedRotatingFileHandler rotates logs daily
        # backupCount=730 keeps logs for 2 years (730 days)
        file_handler = TimedRotatingFileHandler(
            filename=settings.LOG_FILE_PATH,
            when='midnight',  # Rotate at midnight
            interval=1,  # Every 1 day
            backupCount=730,  # Keep 2 years of logs (730 days)
            encoding='utf-8',
            utc=True
        )
        file_handler.setFormatter(formatter)
        file_handler.suffix = "%Y-%m-%d"  # Add date suffix to rotated files
        root_logger.addHandler(file_handler)
    
    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance for a module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)
