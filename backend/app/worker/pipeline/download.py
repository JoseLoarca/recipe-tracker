"""Pipeline stage 1: download the source video and extract its audio."""

import logging
import uuid

import yt_dlp

from app.core.retry import retry_with_backoff
from app.worker.pipeline.errors import PipelineStageError

logger = logging.getLogger(__name__)

# Substrings from yt-dlp's DownloadError messages that indicate a permanent,
# non-retryable failure (the video itself is unavailable) rather than a
# transient network hiccup.
_PRIVATE_MARKERS = ("private video",)
_UNAVAILABLE_MARKERS = ("video unavailable", "has been removed", "no longer available")
_REGION_LOCKED_MARKERS = ("not available in your country", "region")


def _human_message_for(error: yt_dlp.utils.DownloadError) -> str | None:
    """Map a yt-dlp `DownloadError` to a human message, if it's permanent.

    Args:
        error: The exception yt-dlp raised.

    Returns:
        A human-readable message if this failure is permanent (should not
        be retried), or `None` if it looks transient and worth retrying.
    """
    message = str(error).lower()
    if any(marker in message for marker in _PRIVATE_MARKERS):
        return "This video is private."
    if any(marker in message for marker in _UNAVAILABLE_MARKERS):
        return "This video is unavailable or has been removed."
    if any(marker in message for marker in _REGION_LOCKED_MARKERS):
        return "This video is region-locked and not available here."
    return None


def download_audio(source_url: str) -> str:
    """Download a video's audio track via yt-dlp.

    Args:
        source_url: The submitted video link.

    Returns:
        A local filesystem path to the downloaded audio (m4a).

    Raises:
        PipelineStageError: If the video is unavailable, or the download
            keeps failing after retries.
    """
    logger.info("Downloading audio", extra={"source_url": source_url})

    audio_path = f"/tmp/pipeline-audio-{uuid.uuid4().hex}.m4a"
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": audio_path.removesuffix(".m4a") + ".%(ext)s",
        "quiet": True,
        "noplaylist": True,
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "m4a"},
        ],
    }

    def attempt() -> str:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(source_url, download=True)
        except yt_dlp.utils.DownloadError as exc:
            human_message = _human_message_for(exc)
            if human_message is not None:
                raise PipelineStageError(
                    stage="download",
                    input_summary=source_url,
                    human_message=human_message,
                    cause=exc,
                ) from exc
            raise
        return audio_path

    try:
        return retry_with_backoff(attempt, retry_on=yt_dlp.utils.DownloadError)
    except yt_dlp.utils.DownloadError as exc:
        raise PipelineStageError(
            stage="download",
            input_summary=source_url,
            human_message="Could not download this video after retrying.",
            cause=exc,
        ) from exc
