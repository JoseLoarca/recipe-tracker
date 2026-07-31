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
    db.commit()
    db.refresh(membership)
    return membership
