"""
Centralized logging configuration for Pangolin.

Provides console and file logging with consistent formatting.
"""

import logging
import sys
from pathlib import Path


_LOG_FORMAT = "[%(levelname)s] %(asctime)s — %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_initialized = False


def setup_logger(
    name: str = "pangolin",
    log_file: str = "pangolin.log",
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Configure and return the application logger.

    Creates a logger with both console and file handlers.
    Safe to call multiple times — handlers are only added once.

    Args:
        name: Logger name.
        log_file: Path to the log file.
        level: Logging level (default: INFO).

    Returns:
        Configured logger instance.
    """
    global _initialized

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if _initialized:
        return logger

    # Console handler — writes to stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    logger.addHandler(console_handler)

    # File handler — writes to log file
    log_path = Path(log_file)
    file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    logger.addHandler(file_handler)

    _initialized = True

    return logger


def get_logger(name: str = "pangolin") -> logging.Logger:
    """
    Retrieve an existing logger by name.

    If the logger has not been set up yet, initializes it with defaults.

    Args:
        name: Logger name.

    Returns:
        Logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger
