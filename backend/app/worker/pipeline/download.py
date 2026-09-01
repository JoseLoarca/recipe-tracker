"""Pipeline stage 1: download the source video and extract its audio.

Mocked for Milestone 6 (returns a canned local path) — real yt-dlp
integration lands in Milestone 7. The "private"-URL failure case exists
only so the pipeline's error handling can be exercised before yt-dlp
is wired in.
"""

import logging
import uuid

from app.worker.pipeline.errors import PipelineStageError

logger = logging.getLogger(__name__)


def download_audio(source_url: str) -> str:
    """Download a video's audio track.

    Args:
        source_url: The submitted video link.

    Returns:
        A local filesystem path to the downloaded audio.

    Raises:
        PipelineStageError: If the video is unavailable.
    """
    logger.info("Downloading audio", extra={"source_url": source_url})

    if "private" in source_url:
        raise PipelineStageError(
            stage="download",
            input_summary=source_url,
            human_message="This video is private or unavailable.",
        )

    return f"/tmp/mock-audio-{uuid.uuid4().hex}.m4a"
