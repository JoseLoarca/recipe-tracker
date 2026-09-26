"""Handling a submitted video link: queue it for extraction."""

import uuid

from telegram import Update
from telegram.ext import ContextTypes

from app.core.video_url import is_supported_video_url
from app.db.session import SessionLocal
from app.services.recipe_service import create_pending_recipe
from app.services.user_service import get_or_create_user
from app.worker.tasks import process_recipe_submission


async def handle_submit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Queue a submitted video link for the extraction pipeline.

    Ignores messages that don't look like a supported video link, rather
    than replying with an error — a private, single-purpose bot gets all
    sorts of stray messages, and only ones that look like real submissions
    are worth acknowledging.

    Args:
        update: The incoming Telegram update; its text is the candidate link.
        context: The handler context, used to send the reply.
    """
    chat = update.effective_chat
    telegram_user = update.effective_user
    message = update.effective_message
    if chat is None or telegram_user is None or message is None or message.text is None:
        return

    source_url = message.text.strip()
    if not is_supported_video_url(source_url):
        return

    correlation_id = uuid.uuid4()
    with SessionLocal() as db:
        user, _ = get_or_create_user(
            db,
            telegram_chat_id=str(chat.id),
            display_name=telegram_user.full_name or "there",
        )
        recipe = create_pending_recipe(
            db, owner=user, source_url=source_url, correlation_id=correlation_id
        )
        recipe_id = recipe.id

    process_recipe_submission.delay(str(recipe_id), source_url, str(correlation_id), str(chat.id))

    await context.bot.send_message(
        chat_id=chat.id,
        text=f"Queued! Ref: {recipe_id}\nI'll message you when it's ready.",
    )
