# app/logger.py
import logging
import os

# Very noob-friendly logging setup
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logger = logging.getLogger("polygraf")
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

# Avoid duplicate handlers when reloading
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def get_logger(name: str | None = None) -> logging.Logger:
    """Return the root logger or a child logger."""
    return logger if not name else logger.getChild(name)
