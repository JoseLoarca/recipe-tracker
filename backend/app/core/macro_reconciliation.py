"""Aggregating per-ingredient macros into a recipe's per-portion totals."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from app.core.enums import MacroSource


class MacroIngredientLike(Protocol):
    """The subset of `app.db.models.ingredient.Ingredient` this module needs.

    A `Protocol` rather than importing the ORM model directly, so this
    module stays framework-agnostic and easy to unit test with plain objects.
    """

    calories: float | None
    protein_g: float | None
    carbs_g: float | None
    fat_g: float | None
    macro_source: MacroSource


@dataclass(frozen=True)
class RecipeMacroTotals:
    """A recipe's aggregate macros per portion.

    Attributes:
        calories_per_portion: Total calories divided across all portions.
        protein_g_per_portion: Total protein (g) divided across all portions.
        carbs_g_per_portion: Total carbohydrate (g) divided across all portions.
        fat_g_per_portion: Total fat (g) divided across all portions.
        macro_source: Whether every ingredient's macros were USDA-verified,
            every one was LLM-estimated, or the recipe is a mix of both.
    """

    calories_per_portion: float
    protein_g_per_portion: float
    carbs_g_per_portion: float
    fat_g_per_portion: float
    macro_source: MacroSource


def reconcile_macro_source(sources: Sequence[MacroSource]) -> MacroSource:
    """Determine a recipe's overall macro source from its ingredients' sources.

    Args:
        sources: One `MacroSource` per ingredient in the recipe.

    Returns:
        `MacroSource.USDA_VERIFIED` if every ingredient was verified,
        `MacroSource.LLM_ESTIMATED` if every ingredient was estimated,
        otherwise `MacroSource.MIXED`.

    Raises:
        ValueError: If ``sources`` is empty — a recipe needs at least one
            ingredient to have a macro source.
    """
    unique = set(sources)
    if not unique:
        raise ValueError("Cannot reconcile macro source for an empty ingredient list")
    if unique == {MacroSource.USDA_VERIFIED}:
        return MacroSource.USDA_VERIFIED
    if unique == {MacroSource.LLM_ESTIMATED}:
        return MacroSource.LLM_ESTIMATED
    return MacroSource.MIXED


def compute_recipe_macros(
    ingredients: Sequence[MacroIngredientLike], *, portion_count: int
) -> RecipeMacroTotals:
    """Sum a recipe's ingredients into per-portion macro totals.

    Ingredients with a missing (``None``) macro value contribute zero to
    that total, rather than failing the whole computation — a single
    unresolved ingredient shouldn't block the rest of the recipe's macros.

    Args:
        ingredients: The recipe's ingredients, each with resolved (or
            missing) macro values.
        portion_count: How many portions the recipe makes. Must be at
            least 1.

    Returns:
        The recipe's aggregate macros, divided across ``portion_count``.

    Raises:
        ValueError: If ``ingredients`` is empty or ``portion_count`` is
            less than 1.
    """
    if not ingredients:
        raise ValueError("Cannot compute macros for an empty ingredient list")
    if portion_count < 1:
        raise ValueError("portion_count must be at least 1")

    total_calories = sum(i.calories or 0 for i in ingredients)
    total_protein = sum(i.protein_g or 0 for i in ingredients)
    total_carbs = sum(i.carbs_g or 0 for i in ingredients)
    total_fat = sum(i.fat_g or 0 for i in ingredients)

    return RecipeMacroTotals(
        calories_per_portion=total_calories / portion_count,
        protein_g_per_portion=total_protein / portion_count,
        carbs_g_per_portion=total_carbs / portion_count,
        fat_g_per_portion=total_fat / portion_count,
        macro_source=reconcile_macro_source([i.macro_source for i in ingredients]),
    )
