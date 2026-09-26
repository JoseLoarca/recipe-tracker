"""Pipeline stage 4: resolve each ingredient's macros.

USDA FoodData Central is tried first for a verified value; any miss
(timeout, no match, incomplete nutrient data) falls back to an LLM
estimate from the local Ollama model, so a single flaky/rate-limited USDA
lookup never fails the whole submission.
"""

import json
import logging

from app.config import get_settings
from app.core.enums import MacroSource
from app.core.extraction_schema import MacroEstimateSchema
from app.services.ollama_client import get_ollama_client
from app.services.usda_client import lookup_food_macros
from app.worker.pipeline.types import ExtractedIngredient, ResolvedIngredient

logger = logging.getLogger(__name__)

_ESTIMATE_PROMPT = """Estimate the typical macronutrients per 100g of this food: "{name}"

Respond with ONLY a JSON object (no markdown, no commentary) with this exact shape:
{{"calories": <number>, "protein_g": <number>, "carbs_g": <number>, "fat_g": <number>}}"""

# A conservative fallback used only if the LLM estimate itself fails
# (unreachable Ollama, malformed response) — better than leaving an
# ingredient with no macros at all.
_DEFAULT_ESTIMATE = (150.0, 5.0, 15.0, 5.0)


def _estimate_macros_with_llm(name: str) -> tuple[float, float, float, float]:
    """Ask the local LLM for a rough per-100g macro estimate.

    Args:
        name: The ingredient name.

    Returns:
        A `(calories, protein_g, carbs_g, fat_g)` tuple — the LLM's
        estimate, or a conservative default if the LLM call itself fails.
    """
    settings = get_settings()

    def attempt() -> MacroEstimateSchema:
        response = get_ollama_client().chat(
            model=settings.ollama_model,
            messages=[{"role": "user", "content": _ESTIMATE_PROMPT.format(name=name)}],
            format="json",
        )
        content = response["message"]["content"]
        return MacroEstimateSchema.model_validate(json.loads(content))

    try:
        estimate = attempt()
    except Exception as exc:
        logger.warning(
            "LLM macro estimate failed, using conservative default",
            extra={"ingredient_name": name, "error": str(exc)},
        )
        return _DEFAULT_ESTIMATE

    return (estimate.calories, estimate.protein_g, estimate.carbs_g, estimate.fat_g)


def lookup_macros(ingredients: list[ExtractedIngredient]) -> list[ResolvedIngredient]:
    """Resolve macros for a list of extracted ingredients.

    Args:
        ingredients: The recipe's extracted ingredients.

    Returns:
        One `ResolvedIngredient` per input ingredient. Ingredients matched
        in USDA FoodData Central are marked `MacroSource.USDA_VERIFIED`;
        unmatched ones fall back to `MacroSource.LLM_ESTIMATED`.
    """
    resolved = []
    for ingredient in ingredients:
        macros = lookup_food_macros(ingredient.name)

        if macros is not None:
            calories, protein_g, carbs_g, fat_g = macros
            source = MacroSource.USDA_VERIFIED
        else:
            logger.info(
                "No USDA match, falling back to LLM estimate",
                extra={"ingredient_name": ingredient.name},
            )
            calories, protein_g, carbs_g, fat_g = _estimate_macros_with_llm(ingredient.name)
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
