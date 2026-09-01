"""Pipeline stage 2: transcribe the downloaded audio.

Mocked for Milestone 6 (returns a canned transcript) — real faster-whisper
integration lands in Milestone 7.
"""

import logging

from app.worker.pipeline.errors import PipelineStageError

logger = logging.getLogger(__name__)

_CANNED_TRANSCRIPT = (
    "Today we're making a chicken and quinoa bowl. You'll need two pounds of "
    "chicken breast and one cup of quinoa. First cook the quinoa, then grill "
    "the chicken, then combine and serve."
)


def transcribe_audio(audio_path: str) -> str:
    """Transcribe an audio file's spoken narration.

    Args:
        audio_path: Local path to the audio file (from `download_audio`).

    Returns:
        The transcribed narration.

    Raises:
        PipelineStageError: If no speech is detected in the audio.
    """
    logger.info("Transcribing audio", extra={"audio_path": audio_path})

    if "no-speech" in audio_path:
        raise PipelineStageError(
            stage="transcribe",
            input_summary=audio_path,
            human_message="No speech was detected in this video.",
        )

    return _CANNED_TRANSCRIPT
