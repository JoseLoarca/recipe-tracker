from fastapi import APIRouter, HTTPException, Response, status

from app.api.deps import CurrentUserDep, DbSessionDep, SessionTokenCookie
from app.config import get_settings
from app.core.exceptions import CodeAlreadyConsumedError, CodeExpiredError, InvalidCodeError
from app.db.models.user import User
from app.schemas.auth import UserRead, VerifyCodeRequest
from app.services.auth_code_service import SESSION_TTL, delete_session, verify_login_code
from app.services.user_service import get_user_by_id

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
settings = get_settings()


@router.post("/verify-code", response_model=UserRead)
def verify_code(payload: VerifyCodeRequest, response: Response, db: DbSessionDep) -> User:
    try:
        session = verify_login_code(db, code=payload.code)
    except InvalidCodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code") from exc
    except CodeAlreadyConsumedError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Code already used"
        ) from exc
    except CodeExpiredError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code expired") from exc

    response.set_cookie(
        key=settings.session_cookie_name,
        value=session.token,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        max_age=int(SESSION_TTL.total_seconds()),
    )

    user = get_user_by_id(db, user_id=session.user_id)
    assert user is not None  # the session we just created references a real user
    return user


@router.post("/logout")
def logout(
    response: Response, db: DbSessionDep, session_token: SessionTokenCookie = None
) -> dict[str, str]:
    if session_token is not None:
        delete_session(db, token=session_token)
    response.delete_cookie(settings.session_cookie_name)
    return {"status": "logged out"}


@router.get("/me", response_model=UserRead)
def me(current_user: CurrentUserDep) -> User:
    return current_user
