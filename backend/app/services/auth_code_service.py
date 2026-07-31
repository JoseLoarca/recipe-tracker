"""Web login: issuing bot-delivered codes and exchanging them for sessions."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.core.codes import generate_code, generate_session_token, is_expired
from app.core.exceptions import CodeAlreadyConsumedError, CodeExpiredError, InvalidCodeError
from app.db.models.auth_code import AuthCode
from app.db.models.session import Session
from app.db.models.user import User

LOGIN_CODE_TTL = timedelta(minutes=10)
SESSION_TTL = timedelta(days=30)


def issue_login_code(db: DBSession, *, user: User) -> AuthCode:
    """Generate a single-use, 10-minute login code for a user.

    Called by the bot's ``/login`` handler, which DMs the resulting code
    back to the user.

    Args:
        db: Database session.
        user: The user requesting a web login code.

    Returns:
        The newly created `AuthCode`, with the code on its ``code`` attribute.
    """
    auth_code = AuthCode(
        code=generate_code(),
        user_id=user.id,
        expires_at=datetime.now(UTC) + LOGIN_CODE_TTL,
    )
    db.add(auth_code)
    db.commit()
    db.refresh(auth_code)
    return auth_code


def verify_login_code(db: DBSession, *, code: str) -> Session:
    """Redeem a login code, creating a new web session for its owner.

    Args:
        db: Database session.
        code: The login code being redeemed.

    Returns:
        The newly created `Session`, with the cookie value on its
        ``token`` attribute.

    Raises:
        InvalidCodeError: If no login code matches ``code``.
        CodeAlreadyConsumedError: If the code has already been redeemed.
        CodeExpiredError: If the code is past its expiry.
    """
    auth_code = db.execute(select(AuthCode).where(AuthCode.code == code)).scalar_one_or_none()
    if auth_code is None:
        raise InvalidCodeError(f"No login code matching {code!r}")
    if auth_code.consumed_at is not None:
        raise CodeAlreadyConsumedError(f"Login code {code!r} was already used")
    if is_expired(auth_code.expires_at):
        raise CodeExpiredError(f"Login code {code!r} has expired")

    auth_code.consumed_at = datetime.now(UTC)

    now = datetime.now(UTC)
    session = Session(
        user_id=auth_code.user_id,
        token=generate_session_token(),
        created_at=now,
        expires_at=now + SESSION_TTL,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_user_for_session_token(db: DBSession, *, token: str) -> User | None:
    """Resolve a session cookie value to its user, if the session is still valid.

    Args:
        db: Database session.
        token: The session cookie value.

    Returns:
        The `User` the session belongs to, or None if the token doesn't
        match a session, or that session has expired.
    """
    session = db.execute(select(Session).where(Session.token == token)).scalar_one_or_none()
    if session is None or is_expired(session.expires_at):
        return None
    return db.get(User, session.user_id)


def delete_session(db: DBSession, *, token: str) -> None:
    """Delete a session, if one matches the given token.

    Args:
        db: Database session.
        token: The session cookie value to invalidate.
    """
    session = db.execute(select(Session).where(Session.token == token)).scalar_one_or_none()
    if session is not None:
        db.delete(session)
        db.commit()
