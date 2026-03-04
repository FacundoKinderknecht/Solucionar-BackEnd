"""Structured logging configuration for the application.

Call ``configure_logging()`` once at startup (inside the lifespan handler)
before any other module emits log records.
"""
from __future__ import annotations

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """Configure root logger with a structured format and stdout handler.

    Args:
        level: Logging level string (e.g. ``"DEBUG"``, ``"INFO"``).
            Invalid values default to ``INFO``.
    """
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=log_format,
        datefmt=date_format,
        stream=sys.stdout,
    )

    # Silence noisy third-party loggers that produce little value in production.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.WARNING)


# Module-level logger for use within this package.
logger = logging.getLogger("solucionar")
