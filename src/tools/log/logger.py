# src/tools/log/logger.py

"""
Logging Configuration Module

Loads logging settings from `config.json` and initializes a logger instance
for the application. Supports console output, optional file output, and
runtime configuration of level and startup behavior.
"""

import logging
import os
import json
from typing import Any, Dict

# === Load logging configuration from config.json ===
with open("config.json", "r", encoding="utf-8") as f:
    _config: Dict[str, Any] = json.load(f)

_log_cfg = _config.get("logging", {})
LOG_ENABLED: bool = _log_cfg.get("enabled", True)
LOG_LEVEL: str = _log_cfg.get("level", "INFO").upper()
CLEAR_LOG_ON_START: bool = _log_cfg.get("clear_on_start", False)
WRITE_TO_FILE: bool = _log_cfg.get("write_to_file", False)

# === File-based logging settings ===
LOG_DIR: str = "logs"
LOG_FILE: str = "system.log"
LOG_PATH: str = os.path.join(LOG_DIR, LOG_FILE)

# === Initialize the application logger ===
logger = logging.getLogger("LYNK")

if LOG_ENABLED:
    # Configure logger level
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    # Ensure log directory exists
    os.makedirs(LOG_DIR, exist_ok=True)

    # Optionally clear the existing log file at startup
    if CLEAR_LOG_ON_START and os.path.isfile(LOG_PATH):
        open(LOG_PATH, "w", encoding="utf-8").close()

    # Console handler for standard output
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(
        logging.Formatter("[%(levelname)s] %(message)s")
    )
    logger.addHandler(_console_handler)

    # Optional file handler for persistent logs
    if WRITE_TO_FILE:
        _file_handler = logging.FileHandler(LOG_PATH, mode="a", encoding="utf-8")
        _file_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        )
        logger.addHandler(_file_handler)

    # Disable propagation to avoid duplicate entries
    logger.propagate = False

else:
    # No-op logger when logging is disabled
    class _NullLogger:
        def debug(self, *args, **kwargs): pass
        def info(self, *args, **kwargs): pass
        def warning(self, *args, **kwargs): pass
        def error(self, *args, **kwargs): pass
        def critical(self, *args, **kwargs): pass

    logger = _NullLogger()
