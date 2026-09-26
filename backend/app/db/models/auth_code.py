"""The ``auth_codes`` table: single-use codes for logging into the web UI."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuthCode(Base):
    """A one-time code, bot-delivered, proving a browser belongs to a Telegram identity.

    Exchanged for a `app.db.models.session.Session` via
    `app.services.auth_code_service.verify_login_code`.

    Attributes:
        id: Primary key.
        code: The short code sent to the user via Telegram DM.
        user_id: The user this code authenticates.
        expires_at: Codes are short-lived (10 minutes) so a leaked code
            can't be used long after the fact.
        consumed_at: When the code was redeemed, if it has been — codes
            are single-use.
    """

    __tablename__ = "auth_codes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
