"""Recipe ownership and visibility rules — who can see or edit a given recipe.

Kept as pure functions, independent of FastAPI/the ORM session, so they're
cheap to unit test against plain model instances (see
``tests/unit/test_visibility.py``).
"""

from app.core.enums import RecipeVisibility
from app.db.models.recipe import Recipe
from app.db.models.user import User


def can_view(user: User, recipe: Recipe) -> bool:
    """Check whether a user is allowed to view a recipe.

    The owner can always view their own recipe. Otherwise, a household
    member can view it only if it's marked household-visible and the
    member belongs to the same household as the owner.

    Args:
        user: The user requesting to view the recipe.
        recipe: The recipe being viewed.

    Returns:
        True if ``user`` may view ``recipe``.
    """
    if user.id == recipe.owner_user_id:
        return True

    if recipe.visibility != RecipeVisibility.HOUSEHOLD or recipe.household_id is None:
        return False

    membership = user.household_membership
    return membership is not None and membership.household_id == recipe.household_id


def can_edit(user: User, recipe: Recipe) -> bool:
    """Check whether a user is allowed to edit a recipe.

    Editing is owner-only regardless of visibility (see docs/adr/0008) —
    household visibility shares *viewing*, never editing.

    Args:
        user: The user requesting to edit the recipe.
        recipe: The recipe being edited.

    Returns:
        True if ``user`` owns ``recipe``.
    """
    return user.id == recipe.owner_user_id
