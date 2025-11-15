import logging
from logging.handlers import RotatingFileHandler

def get_logger():
    logger = logging.getLogger("backend")
    # handler = RotatingFileHandler("logs/backend.log", maxBytes=5_000_000, backupCount=2)
    handler = RotatingFileHandler("logs/backend.log", maxBytes=5_000_000, backupCount=2, encoding="utf-8")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger