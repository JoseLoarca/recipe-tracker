"""Structured (JSON) logging setup, shared by the API, worker, and bot."""

import logging
import logging.config
import os

from app.config import get_settings

LOG_FILE_PATH = "logs/pipeline.log"


def configure_logging() -> None:
    """Configure the root logger to emit single-line JSON to stdout and a rotated file.

    Every log record is tagged with the current pipeline correlation/recipe
    ID (see `app.worker.logging_context`), or `None` for records emitted
    outside of a pipeline run (e.g. from the API or bot).

    Called once at process startup by each entrypoint (`app.main`,
    `bot.main`, and the Celery worker).
    """
    settings = get_settings()
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "pipeline_context": {
                    "()": "app.worker.logging_context.PipelineContextFilter",
                },
            },
            "formatters": {
                "json": {
                    "()": "pythonjsonlogger.json.JsonFormatter",
                    "format": (
                        "%(asctime)s %(levelname)s %(name)s %(message)s "
                        "%(correlation_id)s %(recipe_id)s"
                    ),
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "filters": ["pipeline_context"],
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "formatter": "json",
                    "filters": ["pipeline_context"],
                    "filename": LOG_FILE_PATH,
                    "maxBytes": 10_000_000,
                    "backupCount": 5,
                },
            },
            "root": {
                "handlers": ["console", "file"],
                "level": settings.log_level,
            },
        }
    )
