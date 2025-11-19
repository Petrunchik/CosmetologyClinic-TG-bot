import logging
from logging.handlers import RotatingFileHandler
import os


def setup_logger(name: str, log_dir: str = "logs"):
    os.makedirs(log_dir, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    file_handler = RotatingFileHandler(
        filename=os.path.join(log_dir, f"{name}.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.ERROR)
    logger.addHandler(file_handler)

    return logger