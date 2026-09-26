"""Shared FastAPI dependencies: DB sessions and the current-user lookup."""

from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from app.config import get_settings
from app.db.models.user import User
from app.db.session import get_db
from app.services.auth_code_service import get_user_for_session_token

settings = get_settings()

DbSessionDep = Annotated[DBSession, Depends(get_db)]
SessionTokenCookie = Annotated[str | None, Cookie(alias=settings.session_cookie_name)]


def get_current_user(db: DbSessionDep, session_token: SessionTokenCookie = None) -> User:
    """Resolve the authenticated user from the session cookie.

    Args:
        db: Database session (injected).
        session_token: The session cookie value, if present (injected).

    Returns:
        The authenticated `User`.

    Raises:
        HTTPException: 401 if there's no cookie, or it doesn't match a
            live session.
    """
    if session_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user = get_user_for_session_token(db, token=session_token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or invalid"
        )
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
