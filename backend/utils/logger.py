"""
logger.py — Logging configuration for the Academic-System application
This module sets up a standardized logging configuration for the entire application.
It uses Python's built-in logging library to create a logger that can be imported and used across
"""

import logging
import sys

LOG_LEVEL = "INFO"

def get_logger(name: str) -> logging.Logger:
    """
    Retrieve a configured logger instance.

    Args:
        name (str): The name of the logger, typically __name__.
    
    Returns:
        logging.logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Prevent adding multiple handlers if the logger is already configured
    if logger.hasHandlers():
        return logger
    
    log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger