"""Celery application definition."""

from celery import Celery

from app.config import get_settings
from app.logging_config import configure_logging

configure_logging()
settings = get_settings()

celery_app = Celery("recipe_tracker", broker=settings.redis_url, backend=settings.redis_url)

# Without this, Celery's worker command installs its own root logging
# handlers on startup (colorized, plain-text) and silently overrides
# configure_logging() above — every pipeline log line would lose its JSON
# structure and its correlation ID. Only caught by dispatching a real task
# through an actual `celery worker` process; a direct/eager function call
# (as in tests) never exercises Celery's own logging setup, so it looked
# fine there.
celery_app.conf.worker_hijack_root_logger = False

# Imported for its side effect of registering tasks with celery_app — not
# unused despite no direct reference below.
import app.worker.tasks  # noqa: E402,F401
