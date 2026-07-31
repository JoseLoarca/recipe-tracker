"""Telegram bot entrypoint (long-polling).

Recipe-link submission and pipeline notifications land in a later milestone
(see PLAN.md §11) — this wires up registration, household setup, and login.
"""

import logging
from typing import Any

from telegram.ext import Application, CommandHandler

from app.config import get_settings
from app.logging_config import configure_logging
from bot.handlers.household import handle_create_household, handle_invite, handle_join_household
from bot.handlers.login import handle_login
from bot.handlers.start import handle_start

configure_logging()
logger = logging.getLogger(__name__)


def build_application(token: str) -> Application[Any, Any, Any, Any, Any, Any]:
    """Build the Telegram `Application` with all command handlers registered.

    Args:
        token: The bot's Telegram API token.

    Returns:
        A configured `Application`, ready for `Application.run_polling`.
    """
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", handle_start))
    application.add_handler(CommandHandler("create_household", handle_create_household))
    application.add_handler(CommandHandler("join", handle_join_household))
    application.add_handler(CommandHandler("invite", handle_invite))
    application.add_handler(CommandHandler("login", handle_login))
    return application


def main() -> None:
    """Start the bot's long-polling loop, or warn and exit if unconfigured."""
    settings = get_settings()
    if not settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN is not set — bot will not start.")
        return

    application = build_application(settings.telegram_bot_token)
    logger.info("Starting Telegram bot (long polling)")
    application.run_polling()


if __name__ == "__main__":
    main()
