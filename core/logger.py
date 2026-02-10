import logging
import sys

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Force UTF-8 encoding for stderr (fixes Unicode issues)
        handler = logging.StreamHandler(sys.stderr)
        # Set encoding via constructor (Python 3.9+) or fallback
        if hasattr(handler, 'encoding'):
            handler.encoding = 'utf-8'
        # Include timestamp and structured format for better traceability
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)-8s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    return logger