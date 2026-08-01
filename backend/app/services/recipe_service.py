"""Recipe CRUD, tag handling, and shopping-list/macro computation."""

import uuid
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.orm import selectinload

from app.core.enums import RecipeStatus, RecipeVisibility
from app.core.exceptions import NoHouseholdError, NotAuthorizedError
from app.core.macro_reconciliation import compute_recipe_macros
from app.core.shopping_list import ShoppingListItem, build_shopping_list
from app.core.tags import normalize_tag_name
from app.core.visibility import can_edit, can_view
from app.db.models.ingredient import Ingredient
from app.db.models.recipe import Recipe
from app.db.models.recipe_macros import RecipeMacros
from app.db.models.step import Step
from app.db.models.tag import Tag
from app.db.models.user import User
from app.schemas.recipe import IngredientWrite, RecipeCreate, RecipeUpdate

_EAGER_LOAD = (
    selectinload(Recipe.steps),
    selectinload(Recipe.ingredients),
    selectinload(Recipe.macros),
    selectinload(Recipe.tags),
)


def _get_or_create_tags(db: DBSession, names: list[str]) -> list[Tag]:
    """Resolve tag names to `Tag` rows, creating any that don't exist yet.

    Args:
        db: Database session.
        names: Raw tag names; normalized before lookup/creation.

    Returns:
        One `Tag` per distinct normalized name.
    """
    normalized = {normalize_tag_name(name) for name in names}
    if not normalized:
        return []

    existing = db.execute(select(Tag).where(Tag.name.in_(normalized))).scalars().all()
    existing_names = {tag.name for tag in existing}

    created = [Tag(name=name) for name in normalized - existing_names]
    for tag in created:
        db.add(tag)
    if created:
        db.flush()

    return [*existing, *created]


def _recompute_macros(recipe: Recipe, *, portion_count: int) -> None:
    """Recompute a recipe's aggregate macros from its current ingredients.

    Args:
        recipe: The recipe to update. Its ``macros`` are replaced.
        portion_count: How many portions the recipe makes.
    """
    totals = compute_recipe_macros(recipe.ingredients, portion_count=portion_count)
    recipe.macros = RecipeMacros(
        portion_count=portion_count,
        calories_per_portion=totals.calories_per_portion,
        protein_g_per_portion=totals.protein_g_per_portion,
        carbs_g_per_portion=totals.carbs_g_per_portion,
        fat_g_per_portion=totals.fat_g_per_portion,
        macro_source=totals.macro_source,
    )


def _apply_ingredients(
    recipe: Recipe, ingredients: list[IngredientWrite], *, portion_count: int
) -> None:
    """Replace a recipe's ingredients and recompute its aggregate macros.

    Args:
        recipe: The recipe to update. Its existing ``ingredients`` and
            ``macros`` are replaced.
        ingredients: The new ingredient list.
        portion_count: How many portions the recipe makes.
    """
    recipe.ingredients = [
        Ingredient(
            raw_text=item.raw_text,
            name=item.name,
            quantity=item.quantity,
            unit=item.unit,
            calories=item.calories,
            protein_g=item.protein_g,
            carbs_g=item.carbs_g,
            fat_g=item.fat_g,
            macro_source=item.macro_source,
            sort_order=index,
        )
        for index, item in enumerate(ingredients)
    ]
    _recompute_macros(recipe, portion_count=portion_count)


def _current_portion_count(recipe: Recipe) -> int:
    """Read a recipe's current portion count, defaulting to 1 before macros exist.

    Args:
        recipe: The recipe whose portion count is needed.

    Returns:
        ``recipe.macros.portion_count`` if macros exist yet, otherwise 1.
    """
    return recipe.macros.portion_count if recipe.macros is not None else 1


def create_recipe(db: DBSession, *, owner: User, data: RecipeCreate) -> Recipe:
    """Create a recipe with its steps, ingredients, macros, and tags.

    Manually created recipes are immediately `RecipeStatus.COMPLETE` — this
    path doesn't go through the extraction pipeline (see Milestone 6+).

    Args:
        db: Database session.
        owner: The user creating the recipe; becomes its owner.
        data: The recipe's fields, as submitted.

    Returns:
        The newly created `Recipe`.

    Raises:
        NoHouseholdError: If ``data.visibility`` is household-visible but
            ``owner`` doesn't belong to a household.
    """
    if data.visibility == RecipeVisibility.HOUSEHOLD and owner.household_membership is None:
        raise NoHouseholdError(f"User {owner.id} has no household to share this recipe with")

    household_id = (
        owner.household_membership.household_id if owner.household_membership is not None else None
    )

    recipe = Recipe(
        owner_user_id=owner.id,
        household_id=household_id,
        visibility=data.visibility,
        name=data.name,
        source_url=data.source_url,
        status=RecipeStatus.COMPLETE,
        correlation_id=uuid.uuid4(),
        steps=[Step(step_number=i + 1, text=text) for i, text in enumerate(data.steps)],
        tags=_get_or_create_tags(db, data.tags),
    )
    db.add(recipe)
    _apply_ingredients(recipe, data.ingredients, portion_count=data.portion_count)

    db.commit()
    db.refresh(recipe)
    return get_recipe(db, recipe_id=recipe.id)  # type: ignore[return-value]


def get_recipe(db: DBSession, *, recipe_id: uuid.UUID) -> Recipe | None:
    """Look up a recipe by primary key, with its steps/ingredients/macros/tags loaded.

    Args:
        db: Database session.
        recipe_id: The recipe's primary key.

    Returns:
        The matching `Recipe`, or None if no such recipe exists.
    """
    return db.execute(
        select(Recipe).where(Recipe.id == recipe_id).options(*_EAGER_LOAD)
    ).scalar_one_or_none()


def list_recipes(
    db: DBSession,
    *,
    current_user: User,
    visibility: Literal["mine", "household", "all"] = "all",
    tag: str | None = None,
    status: RecipeStatus | None = None,
) -> list[Recipe]:
    """List recipes visible to a user, optionally filtered by tag/status.

    Args:
        db: Database session.
        current_user: The requesting user; controls which recipes are visible.
        visibility: ``"mine"`` for only the user's own recipes, ``"household"``
            for only household-visible recipes from the user's household,
            or ``"all"`` for everything the user is allowed to see.
        tag: If given, only recipes carrying this (normalized) tag.
        status: If given, only recipes with this processing status.

    Returns:
        Matching recipes the user is allowed to view, newest first.
    """
    query = select(Recipe).options(*_EAGER_LOAD).order_by(Recipe.created_at.desc())

    if tag is not None:
        query = query.where(Recipe.tags.any(Tag.name == normalize_tag_name(tag)))
    if status is not None:
        query = query.where(Recipe.status == status)

    candidates = db.execute(query).scalars().all()

    if visibility == "mine":
        return [r for r in candidates if r.owner_user_id == current_user.id]
    if visibility == "household":
        return [
            r
            for r in candidates
            if r.owner_user_id != current_user.id and can_view(current_user, r)
        ]
    return [r for r in candidates if can_view(current_user, r)]


def update_recipe(
    db: DBSession, *, recipe: Recipe, current_user: User, data: RecipeUpdate
) -> Recipe:
    """Apply a partial update to a recipe.

    Args:
        db: Database session.
        recipe: The recipe being updated.
        current_user: The user requesting the edit.
        data: Fields to change; unset fields are left as-is.

    Returns:
        The updated `Recipe`.

    Raises:
        NotAuthorizedError: If ``current_user`` doesn't own ``recipe``
            (see docs/adr/0008 — editing is owner-only).
    """
    if not can_edit(current_user, recipe):
        raise NotAuthorizedError(f"User {current_user.id} cannot edit recipe {recipe.id}")

    if data.name is not None:
        recipe.name = data.name
    if data.steps is not None:
        recipe.steps = [Step(step_number=i + 1, text=text) for i, text in enumerate(data.steps)]
    if data.tags is not None:
        recipe.tags = _get_or_create_tags(db, data.tags)

    new_portion_count = (
        data.portion_count if data.portion_count is not None else _current_portion_count(recipe)
    )
    if data.ingredients is not None:
        _apply_ingredients(recipe, data.ingredients, portion_count=new_portion_count)
    elif data.portion_count is not None:
        # Portion count alone still changes each per-portion macro value.
        _recompute_macros(recipe, portion_count=new_portion_count)

    db.commit()
    db.refresh(recipe)
    return get_recipe(db, recipe_id=recipe.id)  # type: ignore[return-value]


def delete_recipe(db: DBSession, *, recipe: Recipe, current_user: User) -> None:
    """Delete a recipe.

    Args:
        db: Database session.
        recipe: The recipe to delete.
        current_user: The user requesting the deletion.

    Raises:
        NotAuthorizedError: If ``current_user`` doesn't own ``recipe``.
    """
    if not can_edit(current_user, recipe):
        raise NotAuthorizedError(f"User {current_user.id} cannot delete recipe {recipe.id}")
    db.delete(recipe)
    db.commit()


def set_recipe_visibility(
    db: DBSession, *, recipe: Recipe, current_user: User, visibility: RecipeVisibility
) -> Recipe:
    """Change a recipe's visibility between personal and household.

    Args:
        db: Database session.
        recipe: The recipe being updated.
        current_user: The user requesting the change.
        visibility: The recipe's new visibility.

    Returns:
        The updated `Recipe`.

    Raises:
        NotAuthorizedError: If ``current_user`` doesn't own ``recipe``.
        NoHouseholdError: If setting household-visibility but the owner
            doesn't belong to a household.
    """
    if not can_edit(current_user, recipe):
        raise NotAuthorizedError(f"User {current_user.id} cannot change recipe {recipe.id}")
    if visibility == RecipeVisibility.HOUSEHOLD and current_user.household_membership is None:
        raise NoHouseholdError(f"User {current_user.id} has no household to share this recipe with")

    recipe.visibility = visibility
    db.commit()
    db.refresh(recipe)
    return get_recipe(db, recipe_id=recipe.id)  # type: ignore[return-value]


def get_shopping_list(recipe: Recipe) -> list[ShoppingListItem]:
    """Build a recipe's deduplicated shopping list from its ingredients.

    Args:
        recipe: The recipe to build a shopping list for.

    Returns:
        One item per distinct ingredient name.
    """
    return build_shopping_list(recipe.ingredients)
