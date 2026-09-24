"""Client for USDA FoodData Central's food-search API.

Used to resolve an ingredient name to verified per-100g macros. Any
failure (timeout, no match, missing nutrient data) returns `None` rather
than raising — the pipeline's macro-lookup stage falls back to an LLM
estimate in that case, so a flaky/rate-limited USDA API never fails a
whole submission.
"""

import logging

import httpx

from app.config import get_settings
from app.core.retry import retry_with_backoff

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

# FoodData Central nutrient IDs for the four macros we track.
_NUTRIENT_IDS = {
    "calories": 1008,
    "protein_g": 1003,
    "carbs_g": 1005,
    "fat_g": 1004,
}


def lookup_food_macros(query: str) -> tuple[float, float, float, float] | None:
    """Look up an ingredient's per-100g macros via USDA FoodData Central.

    Args:
        query: The ingredient name to search for (e.g. "chicken breast").

    Returns:
        A `(calories, protein_g, carbs_g, fat_g)` tuple per 100g, or `None`
        if the request failed, no food matched, or none of the top matches
        reported all four tracked nutrients.
    """
    settings = get_settings()

    def attempt() -> httpx.Response:
        response = httpx.get(
            _SEARCH_URL,
            params={
                "api_key": settings.usda_api_key,
                "query": query,
                "dataType": ["Foundation", "SR Legacy"],
                # Some Foundation-dataset entries omit the basic macro
                # nutrients from search results entirely (they're reported
                # under a different structure) — fetching several
                # candidates and taking the first complete one is more
                # reliable than trusting the top search hit alone.
                "pageSize": 5,
            },
            timeout=10.0,
        )
        response.raise_for_status()
        return response

    try:
        response = retry_with_backoff(attempt, retry_on=httpx.TransportError)
    except httpx.HTTPError as exc:
        logger.warning("USDA lookup failed", extra={"query": query, "error": str(exc)})
        return None

    for food in response.json().get("foods", []):
        nutrients = {
            nutrient["nutrientId"]: nutrient["value"] for nutrient in food.get("foodNutrients", [])
        }
        if all(nutrient_id in nutrients for nutrient_id in _NUTRIENT_IDS.values()):
            return (
                nutrients[_NUTRIENT_IDS["calories"]],
                nutrients[_NUTRIENT_IDS["protein_g"]],
                nutrients[_NUTRIENT_IDS["carbs_g"]],
                nutrients[_NUTRIENT_IDS["fat_g"]],
            )

    return None
