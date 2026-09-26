"""The ``households`` table: an optional shared group of users."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Household(Base):
    """A group of users who can share recipes marked household-visible.

    Attributes:
        id: Primary key.
        name: Display name (e.g. "The Smiths"), chosen at creation.
        created_at: When the household was created.
    """

    __tablename__ = "households"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
