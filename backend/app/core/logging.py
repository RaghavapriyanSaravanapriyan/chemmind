import logging
import sys
from app.core.config import settings


def setup_logging() -> logging.Logger:
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logger = logging.getLogger("chemmind.backend")
    logger.setLevel(log_level)
    return logger


logger = setup_logging()
