"""The ``household_memberships`` table: which user belongs to which household."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.user import User


class HouseholdMembership(Base):
    """Links one user to one household.

    ``user_id`` is unique, enforcing at most one household per user without
    hard-coding an assumption about household size elsewhere in the schema.

    Attributes:
        id: Primary key.
        user_id: The member. Unique — a user belongs to at most one household.
        household_id: The household this user belongs to.
        joined_at: When the membership was created.
        user: The associated `User`.
    """

    __tablename__ = "household_memberships"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True
    )
    household_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("households.id"))
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="household_membership")
