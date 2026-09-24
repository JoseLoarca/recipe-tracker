"""The Celery task orchestrating the video-to-recipe pipeline.

Each stage in `app.worker.pipeline` is still mocked as of Milestone 6
(see PLAN.md §11) — this task proves the orchestration, correlation-ID
logging, and success/failure persistence work end-to-end before the real
yt-dlp/faster-whisper/Ollama/USDA integrations land in Milestone 7.
"""

import logging
import uuid

from app.db.session import SessionLocal
from app.worker.celery_app import celery_app
from app.worker.logging_context import bind_pipeline_context
from app.worker.pipeline.download import download_audio
from app.worker.pipeline.errors import PipelineStageError
from app.worker.pipeline.extract import extract_recipe
from app.worker.pipeline.macros import lookup_macros
from app.worker.pipeline.persist import mark_recipe_failed, persist_recipe
from app.worker.pipeline.transcribe import transcribe_audio

logger = logging.getLogger(__name__)


@celery_app.task(name="process_recipe_submission")  # type: ignore[untyped-decorator]
def process_recipe_submission(recipe_id: str, source_url: str, correlation_id: str) -> None:
    """Run one recipe submission through the full extraction pipeline.

    Runs each stage in sequence — download, transcribe, extract, macro
    lookup, persist — inside a correlation-ID-bound logging context, so
    every log line for this submission can be found by its correlation ID
    alone. On any stage's `PipelineStageError`, the recipe is marked
    failed with a human-readable reason instead; no partial data is ever
    saved.

    Args:
        recipe_id: Primary key of the pending `Recipe` row to fill in.
        source_url: The submitted video link.
        correlation_id: Ties this run's log lines together.
    """
    with bind_pipeline_context(correlation_id=correlation_id, recipe_id=recipe_id):
        logger.info("Pipeline started")
        try:
            audio_path = download_audio(source_url)
            transcript = transcribe_audio(audio_path)
            extracted = extract_recipe(transcript)
            resolved_ingredients = lookup_macros(extracted.ingredients)
        except PipelineStageError as exc:
            logger.error(
                "Pipeline stage failed",
                extra={
                    "stage": exc.stage,
                    "input_summary": exc.input_summary,
                    "cause": str(exc.cause) if exc.cause else None,
                },
            )
            with SessionLocal() as db:
                mark_recipe_failed(
                    db, recipe_id=uuid.UUID(recipe_id), failure_reason=exc.human_message
                )
            return

        with SessionLocal() as db:
            persist_recipe(
                db,
                recipe_id=uuid.UUID(recipe_id),
                extracted=extracted,
                resolved_ingredients=resolved_ingredients,
            )
        logger.info("Pipeline completed")
