"""Pipeline stage 5: write the extracted recipe to the database.

Unlike the other stages, this one is already "real" (not mocked) — it
writes to Postgres via the same models and macro-reconciliation logic
the REST API uses, so there's no follow-up work needed here in
Milestone 7.
"""

import logging
import uuid

from sqlalchemy.orm import Session as DBSession

from app.core.enums import RecipeStatus
from app.core.macro_reconciliation import compute_recipe_macros
from app.db.models.ingredient import Ingredient
from app.db.models.recipe import Recipe
from app.db.models.recipe_macros import RecipeMacros
from app.db.models.step import Step
from app.services.recipe_service import get_or_create_tags
from app.worker.pipeline.types import ExtractedRecipe, ResolvedIngredient

logger = logging.getLogger(__name__)


def persist_recipe(
    db: DBSession,
    *,
    recipe_id: uuid.UUID,
    extracted: ExtractedRecipe,
    resolved_ingredients: list[ResolvedIngredient],
) -> None:
    """Write extracted steps/ingredients/macros/tags onto a pending recipe.

    Args:
        db: Database session.
        recipe_id: Primary key of the pending `Recipe` row to fill in.
        extracted: The recipe's name, steps, and tags.
        resolved_ingredients: The recipe's ingredients, with macros resolved.

    Raises:
        ValueError: If no recipe matches ``recipe_id``.
    """
    recipe = db.get(Recipe, recipe_id)
    if recipe is None:
        raise ValueError(f"No recipe found for id {recipe_id!r}")

    recipe.name = extracted.name
    recipe.steps = [Step(step_number=i + 1, text=text) for i, text in enumerate(extracted.steps)]
    recipe.tags = get_or_create_tags(db, extracted.tags)
    recipe.ingredients = [
        Ingredient(
            raw_text=resolved.ingredient.raw_text,
            name=resolved.ingredient.name,
            quantity=resolved.ingredient.quantity,
            unit=resolved.ingredient.unit,
            calories=resolved.calories,
            protein_g=resolved.protein_g,
            carbs_g=resolved.carbs_g,
            fat_g=resolved.fat_g,
            macro_source=resolved.macro_source,
            sort_order=index,
        )
        for index, resolved in enumerate(resolved_ingredients)
    ]

    totals = compute_recipe_macros(recipe.ingredients, portion_count=extracted.portion_count)
    recipe.macros = RecipeMacros(
        portion_count=extracted.portion_count,
        calories_per_portion=totals.calories_per_portion,
        protein_g_per_portion=totals.protein_g_per_portion,
        carbs_g_per_portion=totals.carbs_g_per_portion,
        fat_g_per_portion=totals.fat_g_per_portion,
        macro_source=totals.macro_source,
    )
    recipe.status = RecipeStatus.COMPLETE

    db.commit()
    logger.info("Recipe saved", extra={"recipe_name": recipe.name})


def mark_recipe_failed(db: DBSession, *, recipe_id: uuid.UUID, failure_reason: str) -> None:
    """Mark a recipe as failed, with a human-readable reason.

    No partial data (steps/ingredients/macros) is ever written for a
    failed recipe — only the failure itself is recorded.

    Args:
        db: Database session.
        recipe_id: Primary key of the `Recipe` row to mark failed.
        failure_reason: A human-readable explanation of what went wrong.

    Raises:
        ValueError: If no recipe matches ``recipe_id``.
    """
    recipe = db.get(Recipe, recipe_id)
    if recipe is None:
        raise ValueError(f"No recipe found for id {recipe_id!r}")

    recipe.status = RecipeStatus.FAILED
    recipe.failure_reason = failure_reason
    db.commit()
    logger.warning("Recipe failed", extra={"failure_reason": failure_reason})
