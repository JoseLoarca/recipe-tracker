"""Recognizing a submitted link as a supported video URL."""

from urllib.parse import urlparse

_SUPPORTED_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}


def is_supported_video_url(text: str) -> bool:
    """Check whether a message looks like a YouTube link worth queuing.

    Args:
        text: The raw message text the bot received.

    Returns:
        `True` if `text` parses as an `http(s)` URL on a supported host.
    """
    parsed = urlparse(text.strip())
    return parsed.scheme in ("http", "https") and parsed.netloc in _SUPPORTED_HOSTS
