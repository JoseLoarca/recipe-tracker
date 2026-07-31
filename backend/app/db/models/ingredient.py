import uuid

from sqlalchemy import Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import MacroSource
from app.db.base import Base


class Ingredient(Base):
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
