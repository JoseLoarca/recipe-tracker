"""Looking up the current user's household and its members."""

from fastapi import APIRouter

from app.api.deps import CurrentUserDep, DbSessionDep
from app.schemas.auth import UserRead
from app.schemas.household import HouseholdMeRead, HouseholdRead
from app.services.household_service import get_household_with_members

router = APIRouter(prefix="/api/v1/households", tags=["households"])


@router.get("/me", response_model=HouseholdMeRead)
def get_my_household(current_user: CurrentUserDep, db: DbSessionDep) -> HouseholdMeRead:
    """Fetch the current user's household and its members.

    Args:
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The user's household (or None) and its member list (empty if none).
    """
    household, members = get_household_with_members(db, user=current_user)
    return HouseholdMeRead(
        household=HouseholdRead.model_validate(household) if household is not None else None,
        members=[UserRead.model_validate(u) for u in members],
    )
