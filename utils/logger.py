import logging
from logging.handlers import RotatingFileHandler
import os


def setup_logger(name: str = __name__) -> logging.Logger:
    """
    Create and configure a logger instance

    Args:
        name: Logger name (defaults to module name)

    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # Create logger instance
    logger = logging.getLogger(name)

    # Skip if logger is already configured
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Create formatters
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")

    # Create and configure file handler
    file_handler = RotatingFileHandler(
        "logs/news_service.log", maxBytes=1024 * 1024, backupCount=5  # 1MB
    )
    file_handler.setFormatter(file_formatter)

    # Create and configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
