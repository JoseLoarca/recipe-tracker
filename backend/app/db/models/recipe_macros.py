"""The ``recipe_macros`` table: per-portion macro totals for a recipe."""

import uuid

from sqlalchemy import Enum, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import MacroSource
from app.db.base import Base


class RecipeMacros(Base):
    """A recipe's aggregate macros per portion, one row per recipe.

    Kept separate from `app.db.models.recipe.Recipe` to keep that table lean.
    ``macro_source`` reflects whether every ingredient's macros were
    USDA-verified, LLM-estimated, or a mix of both (see
    `app.core.macro_reconciliation`).

    Attributes:
        recipe_id: The recipe these totals belong to (primary key — one
            row per recipe).
        portion_count: How many portions the recipe makes.
        calories_per_portion: Calories in one portion.
        protein_g_per_portion: Grams of protein in one portion.
        carbs_g_per_portion: Grams of carbohydrate in one portion.
        fat_g_per_portion: Grams of fat in one portion.
        macro_source: Whether these totals are USDA-verified, LLM-estimated,
            or a mix across ingredients.
    """

    __tablename__ = "recipe_macros"

    recipe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recipes.id"), primary_key=True
    )
    portion_count: Mapped[int] = mapped_column()
    calories_per_portion: Mapped[float] = mapped_column(Numeric(7, 2))
    protein_g_per_portion: Mapped[float] = mapped_column(Numeric(7, 2))
    carbs_g_per_portion: Mapped[float] = mapped_column(Numeric(7, 2))
    fat_g_per_portion: Mapped[float] = mapped_column(Numeric(7, 2))
    macro_source: Mapped[MacroSource] = mapped_column(
        Enum(MacroSource, name="macro_source", native_enum=False)
    )
