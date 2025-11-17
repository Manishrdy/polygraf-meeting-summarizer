import logging
import os
import sys
from app.config import LOG_FILE, LOG_LEVEL

LOG_LEVEL_SETTING = getattr(logging, LOG_LEVEL, logging.INFO)

logger = logging.getLogger("polygraf")
logger.setLevel(LOG_LEVEL_SETTING)

if not logger.handlers:
    formatter_text = "[%(levelname)s] %(asctime)s - %(name)s - %(message)s"
    formatter = logging.Formatter(formatter_text)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOG_LEVEL_SETTING)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    try:
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setLevel(LOG_LEVEL_SETTING)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as error:
        logger.error("Failed to create file handler at %s: %s", LOG_FILE, error)

def get_logger(name=None):
    if name:
        return logger.getChild(name)
    return logger