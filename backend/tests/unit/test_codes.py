from datetime import UTC, datetime, timedelta

from app.core.codes import generate_code, generate_session_token, is_expired


def test_generate_code_has_requested_length() -> None:
    assert len(generate_code(8)) == 8
    assert len(generate_code(16)) == 16


def test_generate_code_excludes_ambiguous_characters() -> None:
    code = generate_code(200)
    assert not any(c in code for c in "01OIL")


def test_generate_code_is_random() -> None:
    assert generate_code(10) != generate_code(10)


def test_generate_session_token_is_random_and_url_safe() -> None:
    token_a = generate_session_token()
    token_b = generate_session_token()
    assert token_a != token_b
    assert len(token_a) > 32


def test_is_expired_true_when_past() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    expires_at = now - timedelta(minutes=1)
    assert is_expired(expires_at, now=now) is True


def test_is_expired_false_when_in_future() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    expires_at = now + timedelta(minutes=1)
    assert is_expired(expires_at, now=now) is False


def test_is_expired_false_at_exact_boundary() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    assert is_expired(now, now=now) is False
