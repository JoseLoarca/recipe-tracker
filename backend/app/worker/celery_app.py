"""Celery application definition.

Placeholder for Milestone 1 scaffolding — pipeline tasks land in Milestone 6+
(see PLAN.md §4, §11).
"""

from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery("recipe_tracker", broker=settings.redis_url, backend=settings.redis_url)
