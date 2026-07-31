import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.db.models.user import User


def get_or_create_user(
    db: DBSession, *, telegram_chat_id: str, display_name: str
) -> tuple[User, bool]:
    """Returns (user, created). A person becomes a user on their first bot contact."""
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
    return db.get(User, user_id)
