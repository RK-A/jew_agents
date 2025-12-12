import logging
import sys
from typing import Optional


def setup_logging(level: int = logging.INFO) -> None:
    """Configure structured logging with context support"""
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def get_logger(name: str, context: Optional[dict] = None) -> logging.Logger:
    """
    Get a logger with optional context information
    
    Args:
        name: Logger name (usually module or class name)
        context: Optional dict with context info (user_id, agent_type, etc.)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if context:
        logger = logging.LoggerAdapter(logger, context)
    
    return logger

