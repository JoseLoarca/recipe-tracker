import uuid

from app.core.enums import RecipeVisibility
from app.core.visibility import can_edit, can_view
from app.db.models.household_membership import HouseholdMembership
from app.db.models.recipe import Recipe
from app.db.models.user import User

HOUSEHOLD_A = uuid.uuid4()
HOUSEHOLD_B = uuid.uuid4()


def make_user(*, household_id: uuid.UUID | None = None) -> User:
    user = User(id=uuid.uuid4(), display_name="Test User", telegram_chat_id=str(uuid.uuid4()))
    if household_id is not None:
        user.household_membership = HouseholdMembership(
            id=uuid.uuid4(), user_id=user.id, household_id=household_id
        )
    else:
        user.household_membership = None
    return user


def make_recipe(
    *,
    owner_id: uuid.UUID,
    visibility: RecipeVisibility,
    household_id: uuid.UUID | None,
) -> Recipe:
    return Recipe(
        id=uuid.uuid4(),
        owner_user_id=owner_id,
        household_id=household_id,
        visibility=visibility,
        name="Test Recipe",
        source_url="https://youtube.com/shorts/abc123",
        correlation_id=uuid.uuid4(),
    )


class TestCanView:
    def test_owner_can_view_personal_recipe(self) -> None:
        owner = make_user()
        recipe = make_recipe(
            owner_id=owner.id, visibility=RecipeVisibility.PERSONAL, household_id=None
        )
        assert can_view(owner, recipe) is True

    def test_owner_can_view_own_household_recipe(self) -> None:
        owner = make_user(household_id=HOUSEHOLD_A)
        recipe = make_recipe(
            owner_id=owner.id,
            visibility=RecipeVisibility.HOUSEHOLD,
            household_id=HOUSEHOLD_A,
        )
        assert can_view(owner, recipe) is True

    def test_household_member_can_view_household_visible_recipe(self) -> None:
        owner = make_user(household_id=HOUSEHOLD_A)
        member = make_user(household_id=HOUSEHOLD_A)
        recipe = make_recipe(
            owner_id=owner.id,
            visibility=RecipeVisibility.HOUSEHOLD,
            household_id=HOUSEHOLD_A,
        )
        assert can_view(member, recipe) is True

    def test_household_member_cannot_view_owners_personal_recipe(self) -> None:
        owner = make_user(household_id=HOUSEHOLD_A)
        member = make_user(household_id=HOUSEHOLD_A)
        recipe = make_recipe(
            owner_id=owner.id, visibility=RecipeVisibility.PERSONAL, household_id=None
        )
        assert can_view(member, recipe) is False

    def test_non_member_cannot_view_household_visible_recipe(self) -> None:
        owner = make_user(household_id=HOUSEHOLD_A)
        outsider = make_user(household_id=HOUSEHOLD_B)
        recipe = make_recipe(
            owner_id=owner.id,
            visibility=RecipeVisibility.HOUSEHOLD,
            household_id=HOUSEHOLD_A,
        )
        assert can_view(outsider, recipe) is False

    def test_user_without_household_cannot_view_household_visible_recipe(self) -> None:
        owner = make_user(household_id=HOUSEHOLD_A)
        solo_user = make_user()
        recipe = make_recipe(
            owner_id=owner.id,
            visibility=RecipeVisibility.HOUSEHOLD,
            household_id=HOUSEHOLD_A,
        )
        assert can_view(solo_user, recipe) is False

    def test_stranger_cannot_view_personal_recipe(self) -> None:
        owner = make_user()
        stranger = make_user()
        recipe = make_recipe(
            owner_id=owner.id, visibility=RecipeVisibility.PERSONAL, household_id=None
        )
        assert can_view(stranger, recipe) is False


class TestCanEdit:
    def test_owner_can_edit_personal_recipe(self) -> None:
        owner = make_user()
        recipe = make_recipe(
            owner_id=owner.id, visibility=RecipeVisibility.PERSONAL, household_id=None
        )
        assert can_edit(owner, recipe) is True

    def test_owner_can_edit_household_visible_recipe(self) -> None:
        owner = make_user(household_id=HOUSEHOLD_A)
        recipe = make_recipe(
            owner_id=owner.id,
            visibility=RecipeVisibility.HOUSEHOLD,
            household_id=HOUSEHOLD_A,
        )
        assert can_edit(owner, recipe) is True

    def test_household_member_cannot_edit_household_visible_recipe(self) -> None:
        owner = make_user(household_id=HOUSEHOLD_A)
        member = make_user(household_id=HOUSEHOLD_A)
        recipe = make_recipe(
            owner_id=owner.id,
            visibility=RecipeVisibility.HOUSEHOLD,
            household_id=HOUSEHOLD_A,
        )
        assert can_edit(member, recipe) is False

    def test_stranger_cannot_edit_personal_recipe(self) -> None:
        owner = make_user()
        stranger = make_user()
        recipe = make_recipe(
            owner_id=owner.id, visibility=RecipeVisibility.PERSONAL, household_id=None
        )
        assert can_edit(stranger, recipe) is False
