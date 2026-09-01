"""Pipeline stage 3: extract a structured recipe from a transcript.

Mocked for Milestone 6 (returns a canned structured recipe regardless of
transcript content) — real Ollama integration lands in Milestone 7 (see
PLAN.md's confirmed stack decisions: the official ``ollama`` Python
library, not a raw HTTP call).
"""

import logging

from app.worker.pipeline.errors import PipelineStageError
from app.worker.pipeline.types import ExtractedIngredient, ExtractedRecipe

logger = logging.getLogger(__name__)


def extract_recipe(transcript: str) -> ExtractedRecipe:
    """Extract a structured recipe from a transcript.

    Args:
        transcript: The video's transcribed narration.

    Returns:
        The extracted recipe: name, steps, ingredients, and tags.

    Raises:
        PipelineStageError: If the transcript is empty.
    """
    logger.info("Extracting recipe", extra={"transcript_length": len(transcript)})

    if not transcript.strip():
        raise PipelineStageError(
            stage="extract",
            input_summary="<empty transcript>",
            human_message="No speech was detected in this video.",
        )

    return ExtractedRecipe(
        name="Chicken and Quinoa Bowl",
        portion_count=2,
        steps=["Cook the quinoa.", "Grill the chicken.", "Combine and serve."],
        ingredients=[
            ExtractedIngredient(
                raw_text="2lbs chicken breast", name="chicken breast", quantity=2, unit="lbs"
            ),
            ExtractedIngredient(raw_text="1 cup quinoa", name="quinoa", quantity=1, unit="cup"),
        ],
        tags=["dinner", "meal-prep"],
    )
