import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

def setup_logging(log_level=logging.INFO, log_dir='logs'):
    """Set up logging configuration for the application"""

    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Set up root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler for general logs
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'sentiment_analysis.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Error file handler
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, 'errors.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    return logger

def get_logger(name):
    """Get a logger instance"""
    return logging.getLogger(name)