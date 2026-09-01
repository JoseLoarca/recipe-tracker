import pytest

from app.core.enums import MacroSource
from app.worker.pipeline.download import download_audio
from app.worker.pipeline.errors import PipelineStageError
from app.worker.pipeline.extract import extract_recipe
from app.worker.pipeline.macros import lookup_macros
from app.worker.pipeline.transcribe import transcribe_audio
from app.worker.pipeline.types import ExtractedIngredient


class TestDownloadAudio:
    def test_returns_a_local_path(self) -> None:
        path = download_audio("https://youtube.com/shorts/abc123")
        assert path.endswith(".m4a")

    def test_raises_for_private_video(self) -> None:
        with pytest.raises(PipelineStageError) as exc_info:
            download_audio("https://youtube.com/shorts/private-video")
        assert exc_info.value.stage == "download"
        assert "private" in exc_info.value.human_message.lower()


class TestTranscribeAudio:
    def test_returns_a_transcript(self) -> None:
        transcript = transcribe_audio("/tmp/audio.m4a")
        assert len(transcript) > 0

    def test_raises_when_no_speech_detected(self) -> None:
        with pytest.raises(PipelineStageError) as exc_info:
            transcribe_audio("/tmp/no-speech-audio.m4a")
        assert exc_info.value.stage == "transcribe"


class TestExtractRecipe:
    def test_returns_a_structured_recipe(self) -> None:
        recipe = extract_recipe("some narration about cooking")
        assert recipe.name
        assert len(recipe.steps) > 0
        assert len(recipe.ingredients) > 0
        assert recipe.portion_count >= 1

    def test_raises_for_empty_transcript(self) -> None:
        with pytest.raises(PipelineStageError) as exc_info:
            extract_recipe("   ")
        assert exc_info.value.stage == "extract"


class TestLookupMacros:
    def test_recognized_ingredient_is_usda_verified(self) -> None:
        resolved = lookup_macros(
            [
                ExtractedIngredient(
                    raw_text="2lbs chicken breast", name="chicken breast", quantity=2, unit="lbs"
                )
            ]
        )
        assert resolved[0].macro_source == MacroSource.USDA_VERIFIED
        assert resolved[0].calories is not None

    def test_unrecognized_ingredient_falls_back_to_estimate(self) -> None:
        resolved = lookup_macros(
            [
                ExtractedIngredient(
                    raw_text="1 tsp fairy dust", name="fairy dust", quantity=1, unit="tsp"
                )
            ]
        )
        assert resolved[0].macro_source == MacroSource.LLM_ESTIMATED

    def test_preserves_ingredient_order(self) -> None:
        ingredients = [
            ExtractedIngredient(raw_text="a", name="chicken breast", quantity=1, unit=None),
            ExtractedIngredient(raw_text="b", name="quinoa", quantity=1, unit=None),
        ]
        resolved = lookup_macros(ingredients)
        assert [r.ingredient.name for r in resolved] == ["chicken breast", "quinoa"]
