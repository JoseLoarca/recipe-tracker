"""The ``ingredients`` table: one row per ingredient in a recipe."""

import uuid

from sqlalchemy import Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import MacroSource
from app.db.base import Base


class Ingredient(Base):
    """One ingredient line, with its extracted quantity and macros.

    Attributes:
        id: Primary key.
        recipe_id: The recipe this ingredient belongs to.
        raw_text: The ingredient as originally extracted (e.g. "2lbs
            chicken breast"), kept for reference alongside the parsed fields.
        name: The parsed ingredient name (e.g. "chicken breast").
        quantity: The parsed numeric quantity, if extractable.
        unit: The parsed unit (e.g. "lbs", "cup"), if extractable.
        calories: This ingredient's calories, given ``quantity``/``unit``.
        protein_g: This ingredient's protein in grams.
        carbs_g: This ingredient's carbohydrate in grams.
        fat_g: This ingredient's fat in grams.
        macro_source: Whether these macros are USDA-verified or LLM-estimated.
        sort_order: Preserves the ingredient list's original order.
    """

    __tablename__ = "ingredients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipe_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("recipes.id"))
    raw_text: Mapped[str] = mapped_column(String(500))
    name: Mapped[str] = mapped_column(String(200))
    quantity: Mapped[float | None] = mapped_column(Numeric(7, 2), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    calories: Mapped[float | None] = mapped_column(Numeric(7, 2), nullable=True)
    protein_g: Mapped[float | None] = mapped_column(Numeric(7, 2), nullable=True)
    carbs_g: Mapped[float | None] = mapped_column(Numeric(7, 2), nullable=True)
    fat_g: Mapped[float | None] = mapped_column(Numeric(7, 2), nullable=True)
    macro_source: Mapped[MacroSource] = mapped_column(
        Enum(MacroSource, name="ingredient_macro_source", native_enum=False)
    )
    sort_order: Mapped[int] = mapped_column()
