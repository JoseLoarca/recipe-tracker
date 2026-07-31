from app.core.enums import RecipeVisibility
from app.db.models.recipe import Recipe
from app.db.models.user import User


def can_view(user: User, recipe: Recipe) -> bool:
    """Owner can always view; a household member can view household-visible recipes only."""
    if user.id == recipe.owner_user_id:
        return True

    if recipe.visibility != RecipeVisibility.HOUSEHOLD or recipe.household_id is None:
        return False

    membership = user.household_membership
    return membership is not None and membership.household_id == recipe.household_id


def can_edit(user: User, recipe: Recipe) -> bool:
    """Editing is owner-only, regardless of visibility (see docs/adr/0008)."""
    return user.id == recipe.owner_user_id
