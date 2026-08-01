"""Recipe CRUD, visibility toggling, and shopping-list endpoints."""

import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUserDep, DbSessionDep
from app.core.enums import RecipeStatus
from app.core.exceptions import NoHouseholdError, NotAuthorizedError
from app.core.visibility import can_view
from app.db.models.recipe import Recipe
from app.schemas.recipe import (
    IngredientRead,
    RecipeCreate,
    RecipeMacrosRead,
    RecipeRead,
    RecipeUpdate,
    RecipeVisibilityUpdate,
    ShoppingListItemRead,
    StepRead,
)
from app.services import recipe_service

router = APIRouter(prefix="/api/v1/recipes", tags=["recipes"])


def _to_read_model(recipe: Recipe) -> RecipeRead:
    """Convert a `Recipe` ORM instance into its API response shape.

    Handled explicitly rather than via Pydantic's ``from_attributes``
    alone, since ``tags`` must be flattened from `Tag` objects to plain
    names.

    Args:
        recipe: The recipe to serialize.

    Returns:
        The recipe's full API representation.
    """
    return RecipeRead(
        id=recipe.id,
        owner_user_id=recipe.owner_user_id,
        household_id=recipe.household_id,
        visibility=recipe.visibility,
        name=recipe.name,
        source_url=recipe.source_url,
        status=recipe.status,
        failure_reason=recipe.failure_reason,
        created_at=recipe.created_at,
        updated_at=recipe.updated_at,
        steps=[StepRead.model_validate(s) for s in recipe.steps],
        ingredients=[IngredientRead.model_validate(i) for i in recipe.ingredients],
        macros=(
            RecipeMacrosRead.model_validate(recipe.macros) if recipe.macros is not None else None
        ),
        tags=[tag.name for tag in recipe.tags],
    )


def _get_visible_recipe_or_404(
    db: DbSessionDep, current_user: CurrentUserDep, recipe_id: uuid.UUID
) -> Recipe:
    """Look up a recipe, hiding its existence from users who can't view it.

    Args:
        db: Database session.
        current_user: The requesting user.
        recipe_id: The recipe's primary key.

    Returns:
        The recipe, if it exists and is visible to ``current_user``.

    Raises:
        HTTPException: 404 if the recipe doesn't exist, or isn't visible
            to ``current_user`` — the same response either way, so a
            personal recipe's existence isn't leaked to other users.
    """
    recipe = recipe_service.get_recipe(db, recipe_id=recipe_id)
    if recipe is None or not can_view(current_user, recipe):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    return recipe


@router.post("", response_model=RecipeRead, status_code=status.HTTP_201_CREATED)
def create_recipe(
    payload: RecipeCreate, current_user: CurrentUserDep, db: DbSessionDep
) -> RecipeRead:
    """Create a recipe owned by the current user.

    Args:
        payload: The recipe's fields.
        current_user: The authenticated user; becomes the recipe's owner.
        db: Database session.

    Returns:
        The newly created recipe.

    Raises:
        HTTPException: 400 if ``payload.visibility`` is household-visible
            but the user has no household.
    """
    try:
        recipe = recipe_service.create_recipe(db, owner=current_user, data=payload)
    except NoHouseholdError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_read_model(recipe)


@router.get("", response_model=list[RecipeRead])
def list_recipes(
    current_user: CurrentUserDep,
    db: DbSessionDep,
    visibility: Annotated[Literal["mine", "household", "all"], Query()] = "all",
    tag: Annotated[str | None, Query()] = None,
    status_filter: Annotated[RecipeStatus | None, Query(alias="status")] = None,
) -> list[RecipeRead]:
    """List recipes visible to the current user.

    Args:
        current_user: The authenticated user.
        db: Database session.
        visibility: ``mine``, ``household``, or ``all`` (default).
        tag: If given, only recipes carrying this tag.
        status_filter: If given (as the ``status`` query param), only
            recipes with this processing status.

    Returns:
        Matching recipes, newest first.
    """
    recipes = recipe_service.list_recipes(
        db, current_user=current_user, visibility=visibility, tag=tag, status=status_filter
    )
    return [_to_read_model(r) for r in recipes]


@router.get("/{recipe_id}", response_model=RecipeRead)
def get_recipe(recipe_id: uuid.UUID, current_user: CurrentUserDep, db: DbSessionDep) -> RecipeRead:
    """Fetch a single recipe's full detail.

    Args:
        recipe_id: The recipe's primary key.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The recipe's full representation.

    Raises:
        HTTPException: 404 if the recipe doesn't exist or isn't visible
            to the current user.
    """
    recipe = _get_visible_recipe_or_404(db, current_user, recipe_id)
    return _to_read_model(recipe)


@router.patch("/{recipe_id}", response_model=RecipeRead)
def update_recipe(
    recipe_id: uuid.UUID, payload: RecipeUpdate, current_user: CurrentUserDep, db: DbSessionDep
) -> RecipeRead:
    """Apply a partial update to a recipe.

    Args:
        recipe_id: The recipe's primary key.
        payload: Fields to change; unset fields are left as-is.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The updated recipe.

    Raises:
        HTTPException: 404 if the recipe doesn't exist or isn't visible
            to the current user; 403 if the user doesn't own it.
    """
    recipe = _get_visible_recipe_or_404(db, current_user, recipe_id)
    try:
        updated = recipe_service.update_recipe(
            db, recipe=recipe, current_user=current_user, data=payload
        )
    except NotAuthorizedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return _to_read_model(updated)


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(recipe_id: uuid.UUID, current_user: CurrentUserDep, db: DbSessionDep) -> None:
    """Delete a recipe.

    Args:
        recipe_id: The recipe's primary key.
        current_user: The authenticated user.
        db: Database session.

    Raises:
        HTTPException: 404 if the recipe doesn't exist or isn't visible
            to the current user; 403 if the user doesn't own it.
    """
    recipe = _get_visible_recipe_or_404(db, current_user, recipe_id)
    try:
        recipe_service.delete_recipe(db, recipe=recipe, current_user=current_user)
    except NotAuthorizedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.patch("/{recipe_id}/visibility", response_model=RecipeRead)
def set_recipe_visibility(
    recipe_id: uuid.UUID,
    payload: RecipeVisibilityUpdate,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> RecipeRead:
    """Change a recipe's visibility between personal and household.

    Args:
        recipe_id: The recipe's primary key.
        payload: The recipe's new visibility.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The updated recipe.

    Raises:
        HTTPException: 404 if the recipe doesn't exist or isn't visible
            to the current user; 403 if the user doesn't own it; 400 if
            setting household-visibility but the user has no household.
    """
    recipe = _get_visible_recipe_or_404(db, current_user, recipe_id)
    try:
        updated = recipe_service.set_recipe_visibility(
            db, recipe=recipe, current_user=current_user, visibility=payload.visibility
        )
    except NotAuthorizedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except NoHouseholdError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_read_model(updated)


@router.get("/{recipe_id}/shopping-list", response_model=list[ShoppingListItemRead])
def get_shopping_list(
    recipe_id: uuid.UUID, current_user: CurrentUserDep, db: DbSessionDep
) -> list[ShoppingListItemRead]:
    """Fetch a recipe's deduplicated shopping list.

    Args:
        recipe_id: The recipe's primary key.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        One item per distinct ingredient name.

    Raises:
        HTTPException: 404 if the recipe doesn't exist or isn't visible
            to the current user.
    """
    recipe = _get_visible_recipe_or_404(db, current_user, recipe_id)
    items = recipe_service.get_shopping_list(recipe)
    return [ShoppingListItemRead.model_validate(item) for item in items]
