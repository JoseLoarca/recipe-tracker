"""User registration and lookup."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.db.models.user import User


def get_or_create_user(
    db: DBSession, *, telegram_chat_id: str, display_name: str
) -> tuple[User, bool]:
    """Look up a user by Telegram chat ID, registering them if they're new.

    A person becomes a user the first time they contact the bot — there is
    no separate signup step (see docs/adr/0007).

    Args:
        db: Database session.
        telegram_chat_id: The Telegram chat ID proving this user's identity.
        display_name: Name to use if this is a new registration.

    Returns:
        A tuple of ``(user, created)``, where ``created`` is True if this
        call just registered a new user.
    """
    existing = db.execute(
        select(User).where(User.telegram_chat_id == telegram_chat_id)
    ).scalar_one_or_none()
    if existing is not None:
        return existing, False

    user = User(telegram_chat_id=telegram_chat_id, display_name=display_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, True


def get_user_by_id(db: DBSession, *, user_id: uuid.UUID) -> User | None:
    """Look up a user by primary key.

    Args:
        db: Database session.
        user_id: The user's primary key.

    Returns:
        The matching `User`, or None if no such user exists.
    """
    return db.get(User, user_id)
