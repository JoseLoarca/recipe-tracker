from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import (
    AlreadyInHouseholdError,
    CodeAlreadyConsumedError,
    CodeExpiredError,
    InvalidCodeError,
)
from app.db.models.user import User
from app.services.household_service import create_household, generate_invite_code, join_household
from app.services.user_service import get_or_create_user


def _make_user(db: Session, chat_id: str) -> User:
    user, _ = get_or_create_user(db, telegram_chat_id=chat_id, display_name="Test User")
    return user


def test_create_household_adds_creator_as_member(db_session: Session) -> None:
    owner = _make_user(db_session, "111")
    household = create_household(db_session, name="The Loarcas", creator=owner)

    db_session.refresh(owner)
    assert owner.household_membership is not None
    assert owner.household_membership.household_id == household.id


def test_create_household_rejects_user_already_in_a_household(db_session: Session) -> None:
    owner = _make_user(db_session, "111")
    create_household(db_session, name="Household A", creator=owner)

    db_session.refresh(owner)
    with pytest.raises(AlreadyInHouseholdError):
        create_household(db_session, name="Household B", creator=owner)


def test_join_household_with_valid_code(db_session: Session) -> None:
    owner = _make_user(db_session, "111")
    household = create_household(db_session, name="The Loarcas", creator=owner)
    invite = generate_invite_code(db_session, household=household, created_by=owner)

    member = _make_user(db_session, "222")
    membership = join_household(db_session, code=invite.code, user=member)

    assert membership.household_id == household.id


def test_join_household_rejects_unknown_code(db_session: Session) -> None:
    member = _make_user(db_session, "222")
    with pytest.raises(InvalidCodeError):
        join_household(db_session, code="DOESNOTEXIST", user=member)


def test_join_household_rejects_already_consumed_code(db_session: Session) -> None:
    owner = _make_user(db_session, "111")
    household = create_household(db_session, name="The Loarcas", creator=owner)
    invite = generate_invite_code(db_session, household=household, created_by=owner)

    first_joiner = _make_user(db_session, "222")
    join_household(db_session, code=invite.code, user=first_joiner)

    second_joiner = _make_user(db_session, "333")
    with pytest.raises(CodeAlreadyConsumedError):
        join_household(db_session, code=invite.code, user=second_joiner)


def test_join_household_rejects_expired_code(db_session: Session) -> None:
    owner = _make_user(db_session, "111")
    household = create_household(db_session, name="The Loarcas", creator=owner)
    invite = generate_invite_code(db_session, household=household, created_by=owner)
    invite.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    db_session.commit()

    member = _make_user(db_session, "222")
    with pytest.raises(CodeExpiredError):
        join_household(db_session, code=invite.code, user=member)


def test_join_household_rejects_user_already_in_a_household(db_session: Session) -> None:
    owner_a = _make_user(db_session, "111")
    household_a = create_household(db_session, name="Household A", creator=owner_a)
    invite_a = generate_invite_code(db_session, household=household_a, created_by=owner_a)

    owner_b = _make_user(db_session, "222")
    create_household(db_session, name="Household B", creator=owner_b)

    db_session.refresh(owner_b)
    with pytest.raises(AlreadyInHouseholdError):
        join_household(db_session, code=invite_a.code, user=owner_b)
