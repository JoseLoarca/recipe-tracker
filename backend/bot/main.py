"""Telegram bot entrypoint (long-polling).

Placeholder for Milestone 1 scaffolding — registration, household, and
submission handlers land in later milestones (see PLAN.md §11).
"""

import logging

from app.config import get_settings
from app.logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)


def main() -> None:
    settings = get_settings()
    if not settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN is not set — bot will not start.")
        return
    logger.info("Bot scaffolding only — handlers not yet implemented.")


if __name__ == "__main__":
    main()
