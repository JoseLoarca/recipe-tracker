"""Pure helpers for generating and checking short-lived codes and tokens."""

import secrets
import string
from datetime import UTC, datetime

# Excludes visually ambiguous characters (0/O, 1/I/l) since these codes are
# meant to be read aloud or typed by hand (Telegram login codes, invite codes).
_CODE_ALPHABET = "".join(c for c in string.ascii_uppercase + string.digits if c not in "01OIL")


def generate_code(length: int = 8) -> str:
    """Generate a random, human-typeable code.

    Args:
        length: Number of characters to generate.

    Returns:
        A random string drawn from an alphabet with ambiguous characters
        removed (e.g. no ``0``/``O``, ``1``/``I``/``L``).
    """
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(length))


def generate_session_token() -> str:
    """Generate a random, URL-safe session token.

    Returns:
        A cryptographically random token suitable for a session cookie
        value — not meant to be typed by hand.
    """
    return secrets.token_urlsafe(32)


def is_expired(expires_at: datetime, *, now: datetime | None = None) -> bool:
    """Check whether a timestamp is in the past.

    Args:
        expires_at: The expiry timestamp to check.
        now: The current time to compare against; defaults to the real
            current time. Overridable so callers can test expiry logic
            deterministically.

    Returns:
        True if ``now`` is strictly after ``expires_at``.
    """
    current = now if now is not None else datetime.now(UTC)
    return current > expires_at
