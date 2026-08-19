import logging
import sys
from ai.config import settings

def setup_logger(name: str = "chemmind.ai") -> logging.Logger:
    """Configures and returns a logger instance for the AI subsystem."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    log_level_str = getattr(settings, "log_level", "INFO").upper()
    level = getattr(logging, log_level_str, logging.INFO)
    logger.setLevel(level)

    return logger

logger = setup_logger()
