"""Structured (JSON) logging setup, shared by the API, worker, and bot."""

import logging
import logging.config

from app.config import get_settings


def configure_logging() -> None:
    """Configure the root logger to emit single-line JSON to stdout.

    Called once at process startup by each entrypoint (`app.main`,
    `bot.main`, and — once built — the Celery worker).
    """
    settings = get_settings()
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": "pythonjsonlogger.json.JsonFormatter",
                    "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                },
            },
            "root": {
                "handlers": ["console"],
                "level": settings.log_level,
            },
        }
    )
