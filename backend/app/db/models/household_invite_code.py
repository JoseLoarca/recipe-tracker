"""The ``household_invite_codes`` table: single-use codes for joining a household."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class HouseholdInviteCode(Base):
    """A shareable code generated via ``/invite`` that a second user redeems to join.

    Attributes:
        id: Primary key.
        code: The short, human-typeable code shared out-of-band (e.g. by text).
        household_id: The household this code grants membership to.
        created_by_user_id: The household member who generated the code.
        expires_at: Codes expire (see `app.services.household_service`) so a
            stale code can't be redeemed indefinitely.
        consumed_by_user_id: Who redeemed the code, if anyone — codes are
            single-use.
    """

    __tablename__ = "household_invite_codes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    household_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("households.id"))
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
