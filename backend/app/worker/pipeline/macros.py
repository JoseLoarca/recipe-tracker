"""Pipeline stage 4: resolve each ingredient's macros.

Mocked for Milestone 6 (returns canned values, alternating verified/
estimated so `core.macro_reconciliation`'s mixed-source logic gets
exercised end-to-end) — real USDA FoodData Central integration (with
LLM-estimate fallback) lands in Milestone 7.
"""

import logging

from app.core.enums import MacroSource
from app.worker.pipeline.types import ExtractedIngredient, ResolvedIngredient

logger = logging.getLogger(__name__)

# Canned per-100g-ish values, just enough to produce plausible totals.
_CANNED_MACROS: dict[str, tuple[float, float, float, float]] = {
    "chicken breast": (800.0, 150.0, 0.0, 20.0),
    "quinoa": (220.0, 8.0, 40.0, 4.0),
}


def lookup_macros(ingredients: list[ExtractedIngredient]) -> list[ResolvedIngredient]:
    """Resolve macros for a list of extracted ingredients.

    Args:
        ingredients: The recipe's extracted ingredients.

    Returns:
        One `ResolvedIngredient` per input ingredient. Ingredients found
        in the canned table are marked `MacroSource.USDA_VERIFIED`;
        unrecognized ones fall back to `MacroSource.LLM_ESTIMATED` with a
        rough guess, mirroring how the real pipeline degrades when USDA
        has no match.
    """
    resolved = []
    for ingredient in ingredients:
        if ingredient.name in _CANNED_MACROS:
            calories, protein_g, carbs_g, fat_g = _CANNED_MACROS[ingredient.name]
            source = MacroSource.USDA_VERIFIED
        else:
            logger.info(
                "No USDA match, falling back to estimate",
                extra={"ingredient_name": ingredient.name},
            )
            calories, protein_g, carbs_g, fat_g = (150.0, 5.0, 15.0, 5.0)
            source = MacroSource.LLM_ESTIMATED

        resolved.append(
            ResolvedIngredient(
                ingredient=ingredient,
                calories=calories,
                protein_g=protein_g,
                carbs_g=carbs_g,
                fat_g=fat_g,
                macro_source=source,
            )
        )
    return resolved
