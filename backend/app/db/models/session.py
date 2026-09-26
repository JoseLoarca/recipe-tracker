"""The ``sessions`` table: backs the web UI's login cookie."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Session(Base):
    """A logged-in web session, created once an `AuthCode` is verified.

    Attributes:
        id: Primary key.
        user_id: The authenticated user.
        token: The opaque, random token stored in the session cookie.
        created_at: When the session was created.
        expires_at: Sessions last 30 days (see
            `app.services.auth_code_service.SESSION_TTL`).
    """

    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
