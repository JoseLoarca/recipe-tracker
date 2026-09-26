"""Pipeline stage 3: extract a structured recipe from a transcript via Ollama."""

import json
import logging

from pydantic import ValidationError

from app.config import get_settings
from app.core.extraction_schema import ExtractionSchema
from app.services.ollama_client import get_ollama_client
from app.worker.pipeline.errors import PipelineStageError
from app.worker.pipeline.types import ExtractedIngredient, ExtractedRecipe

logger = logging.getLogger(__name__)

_BASE_PROMPT = """You are extracting a structured recipe from a cooking video's transcript.

Transcript:
\"\"\"{transcript}\"\"\"

Respond with ONLY a JSON object (no markdown, no commentary) with this exact shape:
{{
  "name": "<recipe title>",
  "portion_count": <integer number of servings>,
  "steps": ["<step 1>", "<step 2>", ...],
  "ingredients": [
    {{"raw_text": "<ingredient line as stated>", "name": "<plain ingredient name>",
      "quantity": <number or null>, "unit": "<unit or null>"}}
  ],
  "tags": ["<short lowercase tag>", ...]
}}"""

_STRICT_SUFFIX = """

Your previous response could not be parsed as valid JSON matching that shape.
Respond with ONLY the raw JSON object — no markdown code fences, no extra text,
no trailing commas, and every field present exactly as specified."""


def _call_model(transcript: str, *, strict: bool) -> ExtractionSchema:
    """Prompt the local LLM for a structured recipe and validate its response.

    Args:
        transcript: The video's transcribed narration.
        strict: Whether to append a stricter formatting reminder, used on
            the one-time retry after a malformed first response.

    Returns:
        The validated extraction.

    Raises:
        PipelineStageError: If the model itself is unreachable.
        ValueError: If the model's response isn't valid JSON matching the
            expected shape (caller may retry once with `strict=True`).
    """
    settings = get_settings()
    prompt = _BASE_PROMPT.format(transcript=transcript)
    if strict:
        prompt += _STRICT_SUFFIX

    try:
        response = get_ollama_client().chat(
            model=settings.ollama_model,
            messages=[{"role": "user", "content": prompt}],
            format="json",
        )
    except Exception as exc:
        raise PipelineStageError(
            stage="extract",
            input_summary=transcript[:200],
            human_message="The local AI model is unreachable — is Ollama running?",
            cause=exc,
        ) from exc

    content = response["message"]["content"]
    try:
        return ExtractionSchema.model_validate(json.loads(content))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError(str(exc)) from exc


def extract_recipe(transcript: str) -> ExtractedRecipe:
    """Extract a structured recipe from a transcript.

    Args:
        transcript: The video's transcribed narration.

    Returns:
        The extracted recipe: name, steps, ingredients, and tags.

    Raises:
        PipelineStageError: If the transcript is empty, the model is
            unreachable, or its response is still malformed after one
            stricter-prompt retry.
    """
    logger.info("Extracting recipe", extra={"transcript_length": len(transcript)})

    if not transcript.strip():
        raise PipelineStageError(
            stage="extract",
            input_summary="<empty transcript>",
            human_message="No speech was detected in this video.",
        )

    try:
        schema = _call_model(transcript, strict=False)
    except ValueError:
        logger.warning("Malformed extraction response, retrying with stricter prompt")
        try:
            schema = _call_model(transcript, strict=True)
        except ValueError as exc:
            raise PipelineStageError(
                stage="extract",
                input_summary=transcript[:200],
                human_message="Could not extract a recipe from this video.",
                cause=exc,
            ) from exc

    return ExtractedRecipe(
        name=schema.name,
        portion_count=schema.portion_count,
        steps=schema.steps,
        ingredients=[
            ExtractedIngredient(
                raw_text=ingredient.raw_text,
                name=ingredient.name,
                quantity=ingredient.quantity,
                unit=ingredient.unit,
            )
            for ingredient in schema.ingredients
        ],
        tags=schema.tags,
    )
