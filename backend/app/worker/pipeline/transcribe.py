"""Pipeline stage 2: transcribe the downloaded audio via faster-whisper."""

import logging

from faster_whisper import WhisperModel

from app.config import get_settings
from app.worker.pipeline.errors import PipelineStageError

logger = logging.getLogger(__name__)

_model: WhisperModel | None = None


def _get_model() -> WhisperModel:
    """Return a process-wide `WhisperModel`, loaded lazily on first use.

    Loading is slow (seconds), so each worker process loads its model once
    and reuses it for every task it processes, rather than per-call.

    Returns:
        The loaded whisper model, sized per `settings.whisper_model_size`.
    """
    global _model
    if _model is None:
        settings = get_settings()
        _model = WhisperModel(settings.whisper_model_size, device="cpu", compute_type="int8")
    return _model


def transcribe_audio(audio_path: str) -> str:
    """Transcribe an audio file's spoken narration.

    Args:
        audio_path: Local path to the audio file (from `download_audio`).

    Returns:
        The transcribed narration.

    Raises:
        PipelineStageError: If no speech is detected, or transcription fails.
    """
    logger.info("Transcribing audio", extra={"audio_path": audio_path})

    try:
        segments, _info = _get_model().transcribe(audio_path)
        transcript = " ".join(segment.text.strip() for segment in segments).strip()
    except Exception as exc:
        raise PipelineStageError(
            stage="transcribe",
            input_summary=audio_path,
            human_message="Could not transcribe this video's audio.",
            cause=exc,
        ) from exc

    if not transcript:
        raise PipelineStageError(
            stage="transcribe",
            input_summary=audio_path,
            human_message="No speech was detected in this video.",
        )

    return transcript
