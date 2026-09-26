"""Sends pipeline completion/failure notifications back to the submitter.

Called from the worker process (`app.worker.tasks`), not the bot's own
long-polling `Application` — the worker has no `Application` instance to
reuse, so this builds a lightweight `telegram.Bot` client of its own for
the single outgoing message.
"""

import asyncio
import logging
import uuid

from telegram import Bot

from app.config import get_settings

logger = logging.getLogger(__name__)


def notify_success(*, chat_id: str, recipe_name: str, recipe_id: uuid.UUID) -> None:
    """Tell the submitter their recipe finished processing.

    Args:
        chat_id: The submitter's Telegram chat id.
        recipe_name: The extracted recipe's title.
        recipe_id: The recipe's primary key, used to link to the web UI.
    """
    settings = get_settings()
    link = f"{settings.frontend_base_url}/recipes/{recipe_id}"
    _send(chat_id=chat_id, text=f'Done! "{recipe_name}" is ready: {link}')


def notify_failure(*, chat_id: str, failure_reason: str) -> None:
    """Tell the submitter their recipe failed to process.

    Args:
        chat_id: The submitter's Telegram chat id.
        failure_reason: A human-readable explanation of what went wrong.
    """
    _send(chat_id=chat_id, text=f"Couldn't process that video: {failure_reason}")


def _send(*, chat_id: str, text: str) -> None:
    """Send a single Telegram message, logging (not raising) on failure.

    A notification failure shouldn't fail an already-completed/failed
    pipeline run — the recipe's own status is the source of truth; the
    Telegram message is a best-effort convenience on top of it.

    Args:
        chat_id: The recipient's Telegram chat id.
        text: The message body.
    """
    settings = get_settings()
    if not settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN not set, skipping notification")
        return

    try:
        asyncio.run(Bot(token=settings.telegram_bot_token).send_message(chat_id=chat_id, text=text))
    except Exception:
        logger.exception("Failed to send Telegram notification", extra={"chat_id": chat_id})
