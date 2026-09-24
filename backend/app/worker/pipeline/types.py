"""Shared data shapes passed between pipeline stages."""

from dataclasses import dataclass

from app.core.enums import MacroSource


@dataclass(frozen=True)
class ExtractedIngredient:
    """One ingredient as extracted from a transcript, before macro lookup.

    Attributes:
        raw_text: The ingredient as extracted (e.g. "2lbs chicken breast").
        name: The parsed ingredient name.
        quantity: The parsed numeric quantity, if extractable.
        unit: The parsed unit, if extractable.
    """

    raw_text: str
    name: str
    quantity: float | None
    unit: str | None


@dataclass(frozen=True)
class ExtractedRecipe:
    """A structured recipe as extracted from a transcript.

    Attributes:
        name: The recipe's title.
        portion_count: How many portions the recipe makes.
        steps: The instruction steps, in order.
        ingredients: The recipe's ingredients.
        tags: Suggested tags.
    """

    name: str
    portion_count: int
    steps: list[str]
    ingredients: list[ExtractedIngredient]
    tags: list[str]


@dataclass(frozen=True)
class ResolvedIngredient:
    """An ingredient with its macros resolved.

    Attributes:
        ingredient: The extracted ingredient this resolution is for.
        calories: Resolved calories, if known.
        protein_g: Resolved protein in grams, if known.
        carbs_g: Resolved carbohydrate in grams, if known.
        fat_g: Resolved fat in grams, if known.
        macro_source: Whether these values are USDA-verified or LLM-estimated.
    """

    ingredient: ExtractedIngredient
    calories: float | None
    protein_g: float | None
    carbs_g: float | None
    fat_g: float | None
    macro_source: MacroSource
