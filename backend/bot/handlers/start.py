from telegram import Update
from telegram.ext import ContextTypes

from app.db.session import SessionLocal
from app.services.user_service import get_or_create_user


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    telegram_user = update.effective_user
    if chat is None or telegram_user is None:
        return

    display_name = telegram_user.full_name or telegram_user.username or "there"
    with SessionLocal() as db:
        user, created = get_or_create_user(
            db, telegram_chat_id=str(chat.id), display_name=display_name
        )

    if created:
        message = (
            f"Welcome, {user.display_name}! You're registered.\n\n"
            "Would you like to create a new household or join one with an invite code?\n"
            "- /create_household <name>\n"
            "- /join <code>\n\n"
            "Or skip that and just send a YouTube Shorts link once you're set up."
        )
    else:
        message = f"Welcome back, {user.display_name}!"

    await context.bot.send_message(chat_id=chat.id, text=message)
