"""
SANJAYA Centralized Logging Module
Handles all application logging to a centralized log file.
"""

import os
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

# ── Log directory setup ──────────────────────────────────────────────────
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# ── Logger configuration ────────────────────────────────────────────────
logger = logging.getLogger("sanjaya")
logger.setLevel(logging.DEBUG)

# ── File handler with rotation (max 10MB, keep 5 backups) ────────────────
file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.DEBUG)

# ── Console handler ──────────────────────────────────────────────────────
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# ── Formatter ────────────────────────────────────────────────────────────
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# ── Add handlers ─────────────────────────────────────────────────────────
logger.addHandler(file_handler)
logger.addHandler(console_handler)


# ── Public logging functions ────────────────────────────────────────────
def log_info(message: str):
    """Log info level message."""
    logger.info(message)


def log_warning(message: str):
    """Log warning level message."""
    logger.warning(message)


def log_error(message: str, exception: Exception = None):
    """Log error level message and optional exception."""
    if exception:
        logger.error(f"{message}: {str(exception)}", exc_info=True)
    else:
        logger.error(message)


def log_debug(message: str):
    """Log debug level message."""
    logger.debug(message)


def log_exception(message: str, exception: Exception):
    """Log exception with traceback."""
    logger.exception(f"{message}: {str(exception)}")


def get_recent_logs(limit: int = 100) -> list[str]:
    """
    Read recent log entries from the log file.
    Returns the last N lines.
    """
    try:
        if not os.path.exists(LOG_FILE):
            return ["No logs available yet."]
        
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()
        
        # Get the last `limit` lines
        recent = lines[-limit:] if len(lines) > limit else lines
        return [line.rstrip() for line in recent]
    except Exception as e:
        return [f"Error reading logs: {str(e)}"]


def clear_logs():
    """Clear all log entries (use with caution in production)."""
    try:
        if os.path.exists(LOG_FILE):
            open(LOG_FILE, 'w').close()
        return True
    except Exception as e:
        logger.error(f"Error clearing logs: {e}")
        return False


# ── Log startup message ──────────────────────────────────────────────────
def log_startup():
    """Log application startup."""
    log_info("=" * 80)
    log_info(f"SANJAYA Application Started - {datetime.now().isoformat()}")
    log_info(f"Log file: {LOG_FILE}")
    log_info("=" * 80)


def log_shutdown():
    """Log application shutdown."""
    log_info("=" * 80)
    log_info(f"SANJAYA Application Shutdown - {datetime.now().isoformat()}")
    log_info("=" * 80)
