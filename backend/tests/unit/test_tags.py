import pytest

from app.core.tags import normalize_tag_name


def test_normalize_tag_name_lowercases_and_trims() -> None:
    assert normalize_tag_name("  Air Fryer  ") == "air fryer"


def test_normalize_tag_name_is_idempotent() -> None:
    assert normalize_tag_name("dinner") == normalize_tag_name(" Dinner ")


def test_normalize_tag_name_rejects_empty_after_trim() -> None:
    with pytest.raises(ValueError, match="empty"):
        normalize_tag_name("   ")
