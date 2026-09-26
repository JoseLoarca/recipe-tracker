from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.main import app
from app.services.auth_code_service import issue_login_code
from app.services.household_service import create_household, generate_invite_code, join_household
from app.services.user_service import get_or_create_user


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_registration_household_and_login_chain(client: TestClient, db_session: Session) -> None:
    # 1. Bot auto-registers the owner on first contact, they create a household.
    owner, owner_created = get_or_create_user(
        db_session, telegram_chat_id="111", display_name="Jose"
    )
    assert owner_created is True

    household = create_household(db_session, name="The Loarcas", creator=owner)
    invite = generate_invite_code(db_session, household=household, created_by=owner)

    # 2. A second person registers and joins via the invite code.
    member, member_created = get_or_create_user(
        db_session, telegram_chat_id="222", display_name="Partner"
    )
    assert member_created is True
    membership = join_household(db_session, code=invite.code, user=member)
    assert membership.household_id == household.id

    # 3. The bot issues a web login code for the member.
    auth_code = issue_login_code(db_session, user=member)

    # 4. The web UI exchanges the code for a session cookie.
    verify_response = client.post("/api/v1/auth/verify-code", json={"code": auth_code.code})
    assert verify_response.status_code == 200
    assert verify_response.json()["display_name"] == "Partner"
    assert "recipe_tracker_session" in verify_response.cookies

    # 5. /me works using the session cookie set on the client.
    me_response = client.get("/api/v1/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["id"] == str(member.id)

    # 6. Logging out clears the session; /me is unauthenticated afterwards.
    logout_response = client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 200

    me_after_logout = client.get("/api/v1/auth/me")
    assert me_after_logout.status_code == 401


def test_verify_code_rejects_invalid_code(client: TestClient) -> None:
    response = client.post("/api/v1/auth/verify-code", json={"code": "NOTREAL"})
    assert response.status_code == 400


def test_me_without_session_is_unauthenticated(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
