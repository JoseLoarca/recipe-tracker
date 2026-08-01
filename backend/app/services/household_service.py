"""Household creation, invite codes, and joining."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.core.codes import generate_code, is_expired
from app.core.exceptions import (
    AlreadyInHouseholdError,
    CodeAlreadyConsumedError,
    CodeExpiredError,
    InvalidCodeError,
)
from app.db.models.household import Household
from app.db.models.household_invite_code import HouseholdInviteCode
from app.db.models.household_membership import HouseholdMembership
from app.db.models.user import User

INVITE_CODE_TTL = timedelta(hours=24)


def create_household(db: DBSession, *, name: str, creator: User) -> Household:
    """Create a household and add its creator as the first member.

    Args:
        db: Database session.
        name: Display name for the new household.
        creator: The user creating the household; becomes its first member.

    Returns:
        The newly created `Household`.

    Raises:
        AlreadyInHouseholdError: If ``creator`` already belongs to a household.
    """
    if creator.household_membership is not None:
        raise AlreadyInHouseholdError(f"User {creator.id} already belongs to a household")

    household = Household(name=name)
    db.add(household)
    db.flush()

    membership = HouseholdMembership(user_id=creator.id, household_id=household.id)
    db.add(membership)
    # Keep the in-memory object in sync: `creator.household_membership` was
    # already lazy-loaded (as None) by the check above, and with
    # expire_on_commit=False a bare commit() won't refresh that cached
    # value — so a stale None would otherwise persist on this object for
    # the rest of the session.
    creator.household_membership = membership
    db.commit()
    db.refresh(household)
    return household


def generate_invite_code(
    db: DBSession, *, household: Household, created_by: User
) -> HouseholdInviteCode:
    """Generate a single-use, 24-hour invite code for a household.

    Args:
        db: Database session.
        household: The household the code will grant membership to.
        created_by: The household member generating the code.

    Returns:
        The newly created `HouseholdInviteCode`, with the shareable code
        on its ``code`` attribute.
    """
    invite = HouseholdInviteCode(
        code=generate_code(),
        household_id=household.id,
        created_by_user_id=created_by.id,
        expires_at=datetime.now(UTC) + INVITE_CODE_TTL,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


def join_household(db: DBSession, *, code: str, user: User) -> HouseholdMembership:
    """Redeem an invite code, adding a user to the household it grants access to.

    Args:
        db: Database session.
        code: The invite code being redeemed.
        user: The user joining the household.

    Returns:
        The newly created `HouseholdMembership`.

    Raises:
        AlreadyInHouseholdError: If ``user`` already belongs to a household.
        InvalidCodeError: If no invite code matches ``code``.
        CodeAlreadyConsumedError: If the code has already been redeemed.
        CodeExpiredError: If the code is past its expiry.
    """
    if user.household_membership is not None:
        raise AlreadyInHouseholdError(f"User {user.id} already belongs to a household")

    invite = db.execute(
        select(HouseholdInviteCode).where(HouseholdInviteCode.code == code)
    ).scalar_one_or_none()
    if invite is None:
        raise InvalidCodeError(f"No invite code matching {code!r}")
    if invite.consumed_by_user_id is not None:
        raise CodeAlreadyConsumedError(f"Invite code {code!r} was already used")
    if is_expired(invite.expires_at):
        raise CodeExpiredError(f"Invite code {code!r} has expired")

    membership = HouseholdMembership(user_id=user.id, household_id=invite.household_id)
    invite.consumed_by_user_id = user.id
    db.add(membership)
    # See the equivalent comment in create_household: keeps the cached
    # relationship value in sync after the check above lazy-loaded it.
    user.household_membership = membership
    db.commit()
    db.refresh(membership)
    return membership


def get_household_with_members(db: DBSession, *, user: User) -> tuple[Household | None, list[User]]:
    """Look up a user's household and its full member list.

    Args:
        db: Database session.
        user: The user whose household is being looked up.

    Returns:
        A tuple of ``(household, members)``. Both are empty/None if the
        user doesn't belong to a household.
    """
    if user.household_membership is None:
        return None, []

    household = db.get(Household, user.household_membership.household_id)
    members = (
        db.execute(
            select(User)
            .join(HouseholdMembership, HouseholdMembership.user_id == User.id)
            .where(HouseholdMembership.household_id == user.household_membership.household_id)
        )
        .scalars()
        .all()
    )
    return household, list(members)
