import logging
import os
import json

# === Load configuration from config.json ===
with open("config.json", "r") as f:
    config = json.load(f)

log_config = config.get("logging", {})
LOG_ENABLED = log_config.get("enabled", True)
LOG_LEVEL = log_config.get("level", "INFO").upper()
CLEAR_LOG_ON_START = log_config.get("clear_on_start", False)
WRITE_TO_FILE = log_config.get("write_to_file", False)  # Default: False

# === Log file settings ===
LOG_DIR = "logs"
LOG_FILE = "system.log"
LOG_PATH = os.path.join(LOG_DIR, LOG_FILE)

# === Create logger instance ===
logger = logging.getLogger("LYNK")

if LOG_ENABLED:
    # Set logging level
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    # Create logs directory if it doesn't exist
    os.makedirs(LOG_DIR, exist_ok=True)

    # Clear the log file at startup if enabled
    if CLEAR_LOG_ON_START and os.path.exists(LOG_PATH):
        open(LOG_PATH, "w").close()

    # Console handler (always active)
    console_handler = logging.StreamHandler()
    console_format = logging.Formatter("[%(levelname)s] %(message)s")
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler (optional)
    if WRITE_TO_FILE:
        file_handler = logging.FileHandler(LOG_PATH, mode="a")
        file_format = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    # Prevent duplicate logs if logger is imported multiple times
    logger.propagate = False

else:
    # Dummy logger for disabling all logging output
    class DummyLogger:
        def debug(self, *args, **kwargs): pass
        def info(self, *args, **kwargs): pass
        def warning(self, *args, **kwargs): pass
        def error(self, *args, **kwargs): pass
        def critical(self, *args, **kwargs): pass

    logger = DummyLogger()
