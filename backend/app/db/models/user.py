"""The ``users`` table: one row per person, per instance."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.household_membership import HouseholdMembership


class User(Base):
    """A registered person.

    There is no password or email — the Telegram chat ID itself is the
    identity, set once at auto-registration (a person's first message to
    the bot) and never changed afterwards.

    Attributes:
        id: Primary key.
        display_name: Name shown in the UI and bot replies.
        telegram_chat_id: The Telegram chat ID that proves this user's
            identity; unique per instance.
        created_at: When this user was auto-registered.
        household_membership: This user's household membership, if any
            (at most one per user).
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_name: Mapped[str] = mapped_column(String(120))
    telegram_chat_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    household_membership: Mapped[HouseholdMembership | None] = relationship(
        back_populates="user", uselist=False
    )
