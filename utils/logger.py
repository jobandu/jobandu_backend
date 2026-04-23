# utils/logger.py
# ─────────────────────────────────────────────────────────────────────────────
# Custom Singleton Logger
#
# File layout:
#   logs/info/info_2026-04-17.log   ← INFO and above
#   logs/error/error_2026-04-17.log ← ERROR and above
#
# Singleton means only ONE logger instance is ever created for the whole app.
# Every time you call AppLogger.get_logger(), you get the same object back.
# ─────────────────────────────────────────────────────────────────────────────

import logging
import os
from datetime import date
from logging.handlers import TimedRotatingFileHandler


class AppLogger:
    """
    Singleton logger class.

    Usage anywhere in the app:
        from utils.logger import AppLogger

        logger = AppLogger.get_logger()
        logger.info("Something happened")
        logger.error("Something went wrong")
    """

    # This class-level variable holds the one and only logger instance.
    # It starts as None and gets created on first call.
    _instance: logging.Logger | None = None

    @classmethod
    def get_logger(cls) -> logging.Logger:
        """
        Returns the shared logger instance.
        Creates it on the first call, reuses it on every call after that.
        """
        if cls._instance is None:
            cls._instance = cls._create_logger()
        return cls._instance

    @classmethod
    def _create_logger(cls) -> logging.Logger:
        """
        Internal method — builds and configures the logger.
        Called only once during the lifetime of the app.
        """

        # Create the root logger for our app
        logger = logging.getLogger("jobandu")
        logger.setLevel(logging.DEBUG)   # Accept everything; handlers decide what to write

        # Don't add duplicate handlers if this gets called more than once
        if logger.handlers:
            return logger

        # ── Log format ────────────────────────────────────────────────────────
        # Example line:
        # [2026-04-17 23:45:01] [INFO ] [main.py:42] Starting up...
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)-5s] [%(filename)s:%(lineno)d] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # ── Create the log directories ────────────────────────────────────────
        os.makedirs("logs/info",  exist_ok=True)
        os.makedirs("logs/error", exist_ok=True)

        # ── Today's date for the filename ─────────────────────────────────────
        today = date.today().isoformat()   # e.g. "2026-04-17"

        # ── INFO file handler ─────────────────────────────────────────────────
        # Writes INFO, WARNING, ERROR, CRITICAL logs to:
        #   logs/info/info_2026-04-17.log
        # Rotates at midnight so each day gets its own file.
        info_handler = TimedRotatingFileHandler(
            filename=f"logs/info/info_{today}.log",
            when="midnight",      # Create a new file every day at midnight
            interval=1,
            backupCount=30,       # Keep last 30 days of info logs
            encoding="utf-8",
        )
        info_handler.setLevel(logging.INFO)
        info_handler.setFormatter(formatter)

        # ── ERROR file handler ────────────────────────────────────────────────
        # Writes ONLY ERROR and CRITICAL logs to:
        #   logs/error/error_2026-04-17.log
        error_handler = TimedRotatingFileHandler(
            filename=f"logs/error/error_{today}.log",
            when="midnight",
            interval=1,
            backupCount=30,       # Keep last 30 days of error logs
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)

        # ── Console handler ───────────────────────────────────────────────────
        # Also print logs to the terminal while running in dev mode
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)

        # ── Attach all handlers to the logger ─────────────────────────────────
        logger.addHandler(info_handler)
        logger.addHandler(error_handler)
        logger.addHandler(console_handler)

        return logger
