from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import CodeAlreadyConsumedError, CodeExpiredError, InvalidCodeError
from app.db.models.user import User
from app.services.auth_code_service import (
    get_user_for_session_token,
    issue_login_code,
    verify_login_code,
)
from app.services.user_service import get_or_create_user


def _make_user(db: Session, chat_id: str = "111") -> User:
    user, _ = get_or_create_user(db, telegram_chat_id=chat_id, display_name="Test User")
    return user


def test_verify_login_code_issues_a_session(db_session: Session) -> None:
    user = _make_user(db_session)
    auth_code = issue_login_code(db_session, user=user)

    session = verify_login_code(db_session, code=auth_code.code)

    assert session.user_id == user.id
    assert get_user_for_session_token(db_session, token=session.token) is not None


def test_verify_login_code_rejects_unknown_code(db_session: Session) -> None:
    with pytest.raises(InvalidCodeError):
        verify_login_code(db_session, code="DOESNOTEXIST")


def test_verify_login_code_rejects_already_consumed_code(db_session: Session) -> None:
    user = _make_user(db_session)
    auth_code = issue_login_code(db_session, user=user)
    verify_login_code(db_session, code=auth_code.code)

    with pytest.raises(CodeAlreadyConsumedError):
        verify_login_code(db_session, code=auth_code.code)


def test_verify_login_code_rejects_expired_code(db_session: Session) -> None:
    user = _make_user(db_session)
    auth_code = issue_login_code(db_session, user=user)
    auth_code.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    db_session.commit()

    with pytest.raises(CodeExpiredError):
        verify_login_code(db_session, code=auth_code.code)


def test_get_user_for_session_token_returns_none_for_unknown_token(db_session: Session) -> None:
    assert get_user_for_session_token(db_session, token="not-a-real-token") is None
