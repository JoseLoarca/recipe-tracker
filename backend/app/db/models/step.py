"""The ``steps`` table: one row per instruction step in a recipe."""

import uuid

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Step(Base):
    """One instruction step in a recipe's method.

    Attributes:
        id: Primary key.
        recipe_id: The recipe this step belongs to.
        step_number: This step's position, 1-indexed.
        text: The instruction text.
    """

    __tablename__ = "steps"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipe_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("recipes.id"))
    step_number: Mapped[int] = mapped_column()
    text: Mapped[str] = mapped_column(Text)
