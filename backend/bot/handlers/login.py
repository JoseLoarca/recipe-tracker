"""The ``/login`` command: issuing a one-time code for the web UI."""

from telegram import Update
from telegram.ext import ContextTypes

from app.db.session import SessionLocal
from app.services.auth_code_service import issue_login_code
from app.services.user_service import get_or_create_user


async def handle_login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Issue a web login code and DM it back to the sender.

    Args:
        update: The incoming Telegram update.
        context: The handler context, used to send the reply.
    """
    chat = update.effective_chat
    telegram_user = update.effective_user
    if chat is None or telegram_user is None:
        return

    with SessionLocal() as db:
        user, _ = get_or_create_user(
            db,
            telegram_chat_id=str(chat.id),
            display_name=telegram_user.full_name or "there",
        )
        auth_code = issue_login_code(db, user=user)

    await context.bot.send_message(
        chat_id=chat.id,
        text=f"Your login code: {auth_code.code}\n"
        "Enter it on the web login page. It expires in 10 minutes.",
    )
