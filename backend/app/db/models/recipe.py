"""The ``recipes`` table: a submitted video and its extraction status."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import RecipeStatus, RecipeVisibility
from app.db.base import Base
from app.db.models.recipe_tag import RecipeTag

if TYPE_CHECKING:
    from app.db.models.ingredient import Ingredient
    from app.db.models.recipe_macros import RecipeMacros
    from app.db.models.step import Step
    from app.db.models.tag import Tag


class Recipe(Base):
    """A recipe submission and its lifecycle through the extraction pipeline.

    ``owner_user_id`` never changes once set; ``visibility`` is the sole
    sharing switch (see `app.core.visibility`). The extracted ingredients,
    steps, and macros live in their own tables (`Ingredient`, `Step`,
    `RecipeMacros`), keeping this row itself lean.

    Attributes:
        id: Primary key.
        owner_user_id: Whoever submitted the source link. Never changes.
        household_id: The owner's household at creation time, if any —
            denormalized here so household-visibility queries don't need a
            join through `HouseholdMembership`.
        visibility: Whether this recipe is visible only to its owner or to
            the whole household.
        name: The recipe's title, as extracted (editable afterwards).
        source_url: The original video link.
        status: Where this submission is in the processing pipeline.
        failure_reason: A human-readable explanation, set only when
            ``status`` is `RecipeStatus.FAILED`.
        correlation_id: Ties every pipeline log line for this submission
            together, from "received" through "saved" or "failed".
        created_at: When the submission was received.
        updated_at: When this row last changed.
        steps: This recipe's instruction steps, ordered by `Step.step_number`.
        ingredients: This recipe's ingredients, ordered by `Ingredient.sort_order`.
        macros: This recipe's aggregate per-portion macros, if computed.
        tags: This recipe's tags.
    """

    __tablename__ = "recipes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    household_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id"), nullable=True
    )
    visibility: Mapped[RecipeVisibility] = mapped_column(
        Enum(RecipeVisibility, name="recipe_visibility", native_enum=False),
        default=RecipeVisibility.PERSONAL,
    )
    name: Mapped[str] = mapped_column(String(200))
    source_url: Mapped[str] = mapped_column(String(2048))
    status: Mapped[RecipeStatus] = mapped_column(
        Enum(RecipeStatus, name="recipe_status", native_enum=False),
        default=RecipeStatus.PENDING,
    )
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    correlation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    steps: Mapped[list[Step]] = relationship(
        order_by="Step.step_number", cascade="all, delete-orphan"
    )
    ingredients: Mapped[list[Ingredient]] = relationship(
        order_by="Ingredient.sort_order", cascade="all, delete-orphan"
    )
    macros: Mapped[RecipeMacros | None] = relationship(uselist=False, cascade="all, delete-orphan")
    tags: Mapped[list[Tag]] = relationship(secondary=RecipeTag.__table__)
