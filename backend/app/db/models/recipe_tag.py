"""The ``recipe_tags`` table: many-to-many join between recipes and tags."""

import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RecipeTag(Base):
    """Associates one recipe with one tag.

    Attributes:
        recipe_id: Half of the composite primary key.
        tag_id: The other half of the composite primary key.
    """

    __tablename__ = "recipe_tags"

    recipe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recipes.id"), primary_key=True
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tags.id"), primary_key=True
    )
