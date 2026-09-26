import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.core.enums import RecipeVisibility
from app.core.exceptions import (
    AlreadyInHouseholdError,
    CodeAlreadyConsumedError,
    CodeExpiredError,
    InvalidCodeError,
    NoHouseholdError,
)
from app.db.models.recipe import Recipe
from app.db.models.user import User
from app.services.household_service import (
    create_household,
    generate_invite_code,
    join_household,
    leave_household,
)
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


def test_leave_household_rejects_a_user_with_no_household(db_session: Session) -> None:
    user = _make_user(db_session, "111")
    with pytest.raises(NoHouseholdError):
        leave_household(db_session, user=user)


def test_leave_household_removes_the_membership(db_session: Session) -> None:
    owner = _make_user(db_session, "111")
    create_household(db_session, name="The Loarcas", creator=owner)
    db_session.refresh(owner)

    leave_household(db_session, user=owner)

    db_session.refresh(owner)
    assert owner.household_membership is None


def test_leave_household_reverts_the_users_shared_recipes_to_personal(db_session: Session) -> None:
    owner = _make_user(db_session, "111")
    household = create_household(db_session, name="The Loarcas", creator=owner)
    db_session.refresh(owner)

    recipe = Recipe(
        owner_user_id=owner.id,
        household_id=household.id,
        visibility=RecipeVisibility.HOUSEHOLD,
        name="Shared Recipe",
        source_url="https://example.com/shared",
        correlation_id=uuid.uuid4(),
    )
    db_session.add(recipe)
    db_session.commit()

    leave_household(db_session, user=owner)

    db_session.refresh(recipe)
    assert recipe.visibility == RecipeVisibility.PERSONAL
    assert recipe.household_id is None


def test_leave_household_does_not_affect_other_members(db_session: Session) -> None:
    owner = _make_user(db_session, "111")
    household = create_household(db_session, name="The Loarcas", creator=owner)
    invite = generate_invite_code(db_session, household=household, created_by=owner)

    partner = _make_user(db_session, "222")
    join_household(db_session, code=invite.code, user=partner)
    db_session.refresh(partner)

    partner_recipe = Recipe(
        owner_user_id=partner.id,
        household_id=household.id,
        visibility=RecipeVisibility.HOUSEHOLD,
        name="Partner's Recipe",
        source_url="https://example.com/partner",
        correlation_id=uuid.uuid4(),
    )
    db_session.add(partner_recipe)
    db_session.commit()

    leave_household(db_session, user=owner)

    db_session.refresh(partner)
    db_session.refresh(partner_recipe)
    assert partner.household_membership is not None
    assert partner.household_membership.household_id == household.id
    assert partner_recipe.visibility == RecipeVisibility.HOUSEHOLD
    assert partner_recipe.household_id == household.id


def test_join_household_rejects_user_already_in_a_household(db_session: Session) -> None:
    owner_a = _make_user(db_session, "111")
    household_a = create_household(db_session, name="Household A", creator=owner_a)
    invite_a = generate_invite_code(db_session, household=household_a, created_by=owner_a)

    owner_b = _make_user(db_session, "222")
    create_household(db_session, name="Household B", creator=owner_b)

    db_session.refresh(owner_b)
    with pytest.raises(AlreadyInHouseholdError):
        join_household(db_session, code=invite_a.code, user=owner_b)
