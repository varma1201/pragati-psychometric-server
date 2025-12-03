"""
Flask Extensions and Utilities for Pragati Psychometric Server

Centralizes logging configuration and Flask utilities
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(app_name: str = "pragati-psychometric") -> logging.Logger:
    """
    Configure application logging with both file and console output
    
    Args:
        app_name: Name of the application for logging
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(app_name)
    logger.setLevel(logging.INFO)
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # File handler (rotating, max 5MB per file, keep 5 backups)
    file_handler = RotatingFileHandler(
        logs_dir / f"{app_name}.log",
        maxBytes=5_000_000,  # 5MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def get_config():
    """
    Get Flask configuration based on environment
    
    Returns:
        Dictionary with Flask configuration
    """
    flask_env = os.getenv("FLASK_ENV", "production")
    
    config = {
        "DEBUG": flask_env == "development",
        "TESTING": flask_env == "testing",
        "JSON_SORT_KEYS": False,
        "SECRET_KEY": os.getenv("SECRET_KEY", "dev-secret-key-psychometric"),
        "PROPAGATE_EXCEPTIONS": True,
        "JSONIFY_PRETTYPRINT_REGULAR": flask_env == "development",
    }
    
    return config


def init_app_config(app):
    """
    Initialize Flask app with configuration
    
    Args:
        app: Flask application instance
    """
    config = get_config()
    for key, value in config.items():
        app.config[key] = value
