import uuid

from sqlalchemy import Enum, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import MacroSource
from app.db.base import Base


class RecipeMacros(Base):
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
