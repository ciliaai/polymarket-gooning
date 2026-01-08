"""
Logging Configuration

Sets up structured logging for the application.
"""

import logging
import sys
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for terminal output"""

    COLORS = {
        "DEBUG": "\033[36m",    # Cyan
        "INFO": "\033[32m",     # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",    # Red
        "CRITICAL": "\033[41m", # Red background
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logger(
    name: str = "ciliaai",
    level: int = logging.INFO,
    log_file: str = None,
) -> logging.Logger:
    """Set up application logger"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers = []

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = ColoredFormatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_format = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger


def log_signal(logger: logging.Logger, signal_type: str, market: str, details: dict):
    """Log a detected signal with structured data"""
    logger.info(
        f"SIGNAL [{signal_type.upper()}] {market[:50]}... "
        f"| magnitude={details.get('magnitude', 'N/A')} "
        f"| confidence={details.get('confidence', 'N/A')}"
    )


def log_post(logger: logging.Logger, success: bool, url: str = None, error: str = None):
    """Log a posting result"""
    if success:
        logger.info(f"POSTED: {url}")
    else:
        logger.error(f"POST FAILED: {error}")
