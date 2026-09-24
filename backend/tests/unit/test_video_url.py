import pytest

from app.core.video_url import is_supported_video_url


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/shorts/abc123",
        "https://youtube.com/watch?v=abc123",
        "https://m.youtube.com/shorts/abc123",
        "https://youtu.be/abc123",
    ],
)
def test_recognizes_supported_hosts(url: str) -> None:
    assert is_supported_video_url(url) is True


@pytest.mark.parametrize(
    "text",
    [
        "hello there",
        "https://vimeo.com/12345",
        "ftp://youtube.com/shorts/abc123",
        "youtube.com/shorts/abc123",  # no scheme
        "",
    ],
)
def test_rejects_unsupported_input(text: str) -> None:
    assert is_supported_video_url(text) is False


def test_strips_surrounding_whitespace() -> None:
    assert is_supported_video_url("  https://youtu.be/abc123  \n") is True
