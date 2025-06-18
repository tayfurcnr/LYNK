# src/tools/log/logger.py

"""
Logging Configuration Module

Loads logging settings from the centralized config manager and initializes
a logger instance for the application. Supports console output, optional
file output, and runtime configuration of level and startup behavior.
"""

import logging
import os

try:
    from src.shared.config.manager import get
    LOG_ENABLED = get("logging.enabled", True)
    LOG_LEVEL = get("logging.level", "INFO").upper()
    CLEAR_LOG_ON_START = get("logging.clear_on_start", False)
    WRITE_TO_FILE = get("logging.write_to_file", False)
except RuntimeError:
    # Config not loaded yet – use default values
    LOG_ENABLED = True
    LOG_LEVEL = "INFO"
    CLEAR_LOG_ON_START = False
    WRITE_TO_FILE = False

# === File-based logging settings ===
LOG_DIR = "logs"
LOG_FILE = "system.log"
LOG_PATH = os.path.join(LOG_DIR, LOG_FILE)

# === Initialize the application logger ===
logger = logging.getLogger("LYNK")

if LOG_ENABLED:
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    os.makedirs(LOG_DIR, exist_ok=True)

    if CLEAR_LOG_ON_START and os.path.isfile(LOG_PATH):
        open(LOG_PATH, "w", encoding="utf-8").close()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("[%(levelname)s] %(message)s")
    )
    logger.addHandler(console_handler)

    if WRITE_TO_FILE:
        file_handler = logging.FileHandler(LOG_PATH, mode="a", encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        )
        logger.addHandler(file_handler)

    logger.propagate = False

else:
    class _NullLogger:
        def debug(self, *args, **kwargs): pass
        def info(self, *args, **kwargs): pass
        def warning(self, *args, **kwargs): pass
        def error(self, *args, **kwargs): pass
        def critical(self, *args, **kwargs): pass

    logger = _NullLogger()
