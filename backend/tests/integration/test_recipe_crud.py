from collections.abc import Callable, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.enums import MacroSource, RecipeVisibility
from app.db.session import get_db
from app.main import app
from app.services.auth_code_service import issue_login_code
from app.services.household_service import create_household, generate_invite_code, join_household
from app.services.user_service import get_or_create_user


@pytest.fixture
def client_factory(db_session: Session) -> Generator[Callable[[], TestClient]]:
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        yield lambda: TestClient(app)
    finally:
        app.dependency_overrides.clear()


def _login(client: TestClient, db_session: Session, user) -> None:  # noqa: ANN001
    auth_code = issue_login_code(db_session, user=user)
    response = client.post("/api/v1/auth/verify-code", json={"code": auth_code.code})
    assert response.status_code == 200


def _make_recipe_payload(**overrides: object) -> dict:
    payload = {
        "name": "Chicken and Quinoa Bowl",
        "source_url": "https://youtube.com/shorts/abc123",
        "portion_count": 2,
        "steps": ["Cook the quinoa.", "Grill the chicken.", "Combine and serve."],
        "ingredients": [
            {
                "raw_text": "2lbs chicken breast",
                "name": "chicken breast",
                "quantity": 2,
                "unit": "lbs",
                "calories": 800,
                "protein_g": 150,
                "carbs_g": 0,
                "fat_g": 20,
                "macro_source": MacroSource.USDA_VERIFIED,
            },
            {
                "raw_text": "1 cup quinoa",
                "name": "quinoa",
                "quantity": 1,
                "unit": "cup",
                "calories": 220,
                "protein_g": 8,
                "carbs_g": 40,
                "fat_g": 4,
                "macro_source": MacroSource.USDA_VERIFIED,
            },
        ],
        "tags": ["dinner", "meal-prep"],
    }
    payload.update(overrides)
    return payload


def test_create_and_get_recipe(
    client_factory: Callable[[], TestClient], db_session: Session
) -> None:
    owner, _ = get_or_create_user(db_session, telegram_chat_id="111", display_name="Owner")
    client = client_factory()
    _login(client, db_session, owner)

    create_response = client.post("/api/v1/recipes", json=_make_recipe_payload())
    assert create_response.status_code == 201
    body = create_response.json()
    assert body["name"] == "Chicken and Quinoa Bowl"
    assert body["visibility"] == "personal"
    assert len(body["ingredients"]) == 2
    assert len(body["steps"]) == 3
    assert body["macros"]["macro_source"] == "usda_verified"
    assert body["macros"]["calories_per_portion"] == 510  # (800 + 220) / 2
    assert set(body["tags"]) == {"dinner", "meal-prep"}

    get_response = client.get(f"/api/v1/recipes/{body['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == body["id"]


def test_recipe_not_visible_to_a_stranger(
    client_factory: Callable[[], TestClient], db_session: Session
) -> None:
    owner, _ = get_or_create_user(db_session, telegram_chat_id="111", display_name="Owner")
    stranger, _ = get_or_create_user(db_session, telegram_chat_id="222", display_name="Stranger")

    owner_client = client_factory()
    _login(owner_client, db_session, owner)
    recipe_id = owner_client.post("/api/v1/recipes", json=_make_recipe_payload()).json()["id"]

    stranger_client = client_factory()
    _login(stranger_client, db_session, stranger)
    response = stranger_client.get(f"/api/v1/recipes/{recipe_id}")
    assert response.status_code == 404


def test_household_member_can_view_household_visible_recipe(
    client_factory: Callable[[], TestClient], db_session: Session
) -> None:
    owner, _ = get_or_create_user(db_session, telegram_chat_id="111", display_name="Owner")
    household = create_household(db_session, name="The Loarcas", creator=owner)
    invite = generate_invite_code(db_session, household=household, created_by=owner)

    member, _ = get_or_create_user(db_session, telegram_chat_id="222", display_name="Member")
    join_household(db_session, code=invite.code, user=member)

    owner_client = client_factory()
    _login(owner_client, db_session, owner)
    recipe_id = owner_client.post(
        "/api/v1/recipes", json=_make_recipe_payload(visibility=RecipeVisibility.HOUSEHOLD)
    ).json()["id"]

    member_client = client_factory()
    _login(member_client, db_session, member)
    response = member_client.get(f"/api/v1/recipes/{recipe_id}")
    assert response.status_code == 200


def test_create_household_visible_recipe_without_a_household_fails(
    client_factory: Callable[[], TestClient], db_session: Session
) -> None:
    owner, _ = get_or_create_user(db_session, telegram_chat_id="111", display_name="Owner")
    client = client_factory()
    _login(client, db_session, owner)

    response = client.post(
        "/api/v1/recipes", json=_make_recipe_payload(visibility=RecipeVisibility.HOUSEHOLD)
    )
    assert response.status_code == 400


def test_list_recipes_filters_by_mine_and_tag(
    client_factory: Callable[[], TestClient], db_session: Session
) -> None:
    owner, _ = get_or_create_user(db_session, telegram_chat_id="111", display_name="Owner")
    other, _ = get_or_create_user(db_session, telegram_chat_id="222", display_name="Other")

    owner_client = client_factory()
    _login(owner_client, db_session, owner)
    owner_client.post("/api/v1/recipes", json=_make_recipe_payload(tags=["breakfast"]))

    other_client = client_factory()
    _login(other_client, db_session, other)
    other_client.post("/api/v1/recipes", json=_make_recipe_payload(tags=["dinner"]))

    mine = owner_client.get("/api/v1/recipes", params={"visibility": "mine"}).json()
    assert len(mine) == 1
    assert mine[0]["owner_user_id"] == str(owner.id)

    tagged = owner_client.get("/api/v1/recipes", params={"tag": "breakfast"}).json()
    assert len(tagged) == 1
    assert "breakfast" in tagged[0]["tags"]


def test_update_recipe_recomputes_macros(
    client_factory: Callable[[], TestClient], db_session: Session
) -> None:
    owner, _ = get_or_create_user(db_session, telegram_chat_id="111", display_name="Owner")
    client = client_factory()
    _login(client, db_session, owner)
    recipe_id = client.post("/api/v1/recipes", json=_make_recipe_payload()).json()["id"]

    response = client.patch(
        f"/api/v1/recipes/{recipe_id}",
        json={
            "ingredients": [
                {
                    "raw_text": "1lb frozen vegetables",
                    "name": "frozen vegetables",
                    "quantity": 1,
                    "unit": "lb",
                    "calories": 100,
                    "protein_g": 5,
                    "carbs_g": 20,
                    "fat_g": 0,
                    "macro_source": MacroSource.LLM_ESTIMATED,
                }
            ]
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["ingredients"]) == 1
    assert body["macros"]["macro_source"] == "llm_estimated"
    assert body["macros"]["calories_per_portion"] == 50  # 100 / portion_count(2)


def test_non_owner_cannot_edit_recipe(
    client_factory: Callable[[], TestClient], db_session: Session
) -> None:
    owner, _ = get_or_create_user(db_session, telegram_chat_id="111", display_name="Owner")
    household = create_household(db_session, name="The Loarcas", creator=owner)
    invite = generate_invite_code(db_session, household=household, created_by=owner)
    member, _ = get_or_create_user(db_session, telegram_chat_id="222", display_name="Member")
    join_household(db_session, code=invite.code, user=member)

    owner_client = client_factory()
    _login(owner_client, db_session, owner)
    recipe_id = owner_client.post(
        "/api/v1/recipes", json=_make_recipe_payload(visibility=RecipeVisibility.HOUSEHOLD)
    ).json()["id"]

    member_client = client_factory()
    _login(member_client, db_session, member)
    response = member_client.patch(f"/api/v1/recipes/{recipe_id}", json={"name": "Hijacked"})
    assert response.status_code == 403


def test_set_visibility_and_delete_recipe(
    client_factory: Callable[[], TestClient], db_session: Session
) -> None:
    owner, _ = get_or_create_user(db_session, telegram_chat_id="111", display_name="Owner")
    household = create_household(db_session, name="The Loarcas", creator=owner)

    client = client_factory()
    _login(client, db_session, owner)
    recipe_id = client.post("/api/v1/recipes", json=_make_recipe_payload()).json()["id"]

    visibility_response = client.patch(
        f"/api/v1/recipes/{recipe_id}/visibility", json={"visibility": "household"}
    )
    assert visibility_response.status_code == 200
    assert visibility_response.json()["visibility"] == "household"
    assert visibility_response.json()["household_id"] == str(household.id)

    delete_response = client.delete(f"/api/v1/recipes/{recipe_id}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/v1/recipes/{recipe_id}")
    assert get_response.status_code == 404


def test_non_owner_cannot_delete_or_change_visibility(
    client_factory: Callable[[], TestClient], db_session: Session
) -> None:
    owner, _ = get_or_create_user(db_session, telegram_chat_id="111", display_name="Owner")
    household = create_household(db_session, name="The Loarcas", creator=owner)
    invite = generate_invite_code(db_session, household=household, created_by=owner)
    member, _ = get_or_create_user(db_session, telegram_chat_id="222", display_name="Member")
    join_household(db_session, code=invite.code, user=member)

    owner_client = client_factory()
    _login(owner_client, db_session, owner)
    recipe_id = owner_client.post(
        "/api/v1/recipes", json=_make_recipe_payload(visibility=RecipeVisibility.HOUSEHOLD)
    ).json()["id"]

    member_client = client_factory()
    _login(member_client, db_session, member)

    visibility_response = member_client.patch(
        f"/api/v1/recipes/{recipe_id}/visibility", json={"visibility": "personal"}
    )
    assert visibility_response.status_code == 403

    delete_response = member_client.delete(f"/api/v1/recipes/{recipe_id}")
    assert delete_response.status_code == 403


def test_shopping_list_endpoint_dedupes_ingredients(
    client_factory: Callable[[], TestClient], db_session: Session
) -> None:
    owner, _ = get_or_create_user(db_session, telegram_chat_id="111", display_name="Owner")
    client = client_factory()
    _login(client, db_session, owner)

    payload = _make_recipe_payload(
        ingredients=[
            {
                "raw_text": "1 tsp salt",
                "name": "salt",
                "macro_source": MacroSource.USDA_VERIFIED,
            },
            {
                "raw_text": "1 tsp salt again",
                "name": "Salt",
                "macro_source": MacroSource.USDA_VERIFIED,
            },
        ]
    )
    recipe_id = client.post("/api/v1/recipes", json=payload).json()["id"]

    response = client.get(f"/api/v1/recipes/{recipe_id}/shopping-list")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["name"] == "salt"


def test_households_me_endpoint(
    client_factory: Callable[[], TestClient], db_session: Session
) -> None:
    owner, _ = get_or_create_user(db_session, telegram_chat_id="111", display_name="Owner")
    create_household(db_session, name="The Loarcas", creator=owner)

    client = client_factory()
    _login(client, db_session, owner)

    response = client.get("/api/v1/households/me")
    assert response.status_code == 200
    body = response.json()
    assert body["household"]["name"] == "The Loarcas"
    assert len(body["members"]) == 1


def test_tags_endpoint_lists_all_tags(
    client_factory: Callable[[], TestClient], db_session: Session
) -> None:
    owner, _ = get_or_create_user(db_session, telegram_chat_id="111", display_name="Owner")
    client = client_factory()
    _login(client, db_session, owner)
    client.post("/api/v1/recipes", json=_make_recipe_payload(tags=["dinner", "meal-prep"]))

    response = client.get("/api/v1/tags")
    assert response.status_code == 200
    assert set(response.json()) == {"dinner", "meal-prep"}
