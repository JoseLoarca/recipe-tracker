import secrets
import string
from datetime import UTC, datetime

# Excludes visually ambiguous characters (0/O, 1/I/l) since these codes are
# meant to be read aloud or typed by hand (Telegram login codes, invite codes).
_CODE_ALPHABET = "".join(c for c in string.ascii_uppercase + string.digits if c not in "01OIL")


def generate_code(length: int = 8) -> str:
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(length))


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def is_expired(expires_at: datetime, *, now: datetime | None = None) -> bool:
    current = now if now is not None else datetime.now(UTC)
    return current > expires_at
