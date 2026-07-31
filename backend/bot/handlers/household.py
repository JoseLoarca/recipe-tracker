from telegram import Update
from telegram.ext import ContextTypes

from app.core.exceptions import (
    AlreadyInHouseholdError,
    CodeAlreadyConsumedError,
    CodeExpiredError,
    InvalidCodeError,
)
from app.db.models.household import Household
from app.db.session import SessionLocal
from app.services.household_service import create_household, generate_invite_code, join_household
from app.services.user_service import get_or_create_user


async def handle_create_household(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    telegram_user = update.effective_user
    if chat is None or telegram_user is None:
        return

    if not context.args:
        await context.bot.send_message(chat_id=chat.id, text="Usage: /create_household <name>")
        return
    name = " ".join(context.args)

    with SessionLocal() as db:
        user, _ = get_or_create_user(
            db,
            telegram_chat_id=str(chat.id),
            display_name=telegram_user.full_name or "there",
        )
        try:
            household = create_household(db, name=name, creator=user)
        except AlreadyInHouseholdError:
            await context.bot.send_message(chat_id=chat.id, text="You're already in a household.")
            return

    await context.bot.send_message(
        chat_id=chat.id,
        text=f"Household '{household.name}' created! Use /invite to get a code to share.",
    )


async def handle_join_household(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    telegram_user = update.effective_user
    if chat is None or telegram_user is None:
        return

    if not context.args:
        await context.bot.send_message(chat_id=chat.id, text="Usage: /join <code>")
        return
    code = context.args[0]

    with SessionLocal() as db:
        user, _ = get_or_create_user(
            db,
            telegram_chat_id=str(chat.id),
            display_name=telegram_user.full_name or "there",
        )
        try:
            join_household(db, code=code, user=user)
        except AlreadyInHouseholdError:
            await context.bot.send_message(chat_id=chat.id, text="You're already in a household.")
            return
        except InvalidCodeError:
            await context.bot.send_message(chat_id=chat.id, text="That invite code doesn't exist.")
            return
        except CodeAlreadyConsumedError:
            await context.bot.send_message(
                chat_id=chat.id, text="That invite code was already used."
            )
            return
        except CodeExpiredError:
            await context.bot.send_message(chat_id=chat.id, text="That invite code has expired.")
            return

    await context.bot.send_message(chat_id=chat.id, text="You've joined the household!")


async def handle_invite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        if user.household_membership is None:
            await context.bot.send_message(
                chat_id=chat.id, text="You need to create or join a household first."
            )
            return

        household = db.get(Household, user.household_membership.household_id)
        assert household is not None  # membership always points at a real household
        invite = generate_invite_code(db, household=household, created_by=user)

    await context.bot.send_message(
        chat_id=chat.id,
        text=f"Invite code: {invite.code}\nShare it with your household member — "
        "it expires in 24 hours.",
    )
