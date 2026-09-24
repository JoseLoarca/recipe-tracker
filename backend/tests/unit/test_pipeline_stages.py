import json
from unittest.mock import MagicMock, patch

import httpx
import pytest
import yt_dlp

from app.core.enums import MacroSource
from app.worker.pipeline.download import download_audio
from app.worker.pipeline.errors import PipelineStageError
from app.worker.pipeline.extract import extract_recipe
from app.worker.pipeline.macros import lookup_macros
from app.worker.pipeline.transcribe import transcribe_audio
from app.worker.pipeline.types import ExtractedIngredient

_VALID_EXTRACTION_JSON = json.dumps(
    {
        "name": "Chicken and Quinoa Bowl",
        "portion_count": 2,
        "steps": ["Cook the quinoa.", "Grill the chicken.", "Combine and serve."],
        "ingredients": [
            {
                "raw_text": "2lbs chicken breast",
                "name": "chicken breast",
                "quantity": 2,
                "unit": "lbs",
            },
            {"raw_text": "1 cup quinoa", "name": "quinoa", "quantity": 1, "unit": "cup"},
        ],
        "tags": ["dinner", "meal-prep"],
    }
)


def _chat_response(content: str) -> dict[str, dict[str, str]]:
    return {"message": {"content": content}}


class TestDownloadAudio:
    @patch("app.worker.pipeline.download.yt_dlp.YoutubeDL")
    def test_returns_a_local_path(self, mock_ydl_cls: MagicMock) -> None:
        mock_ydl_cls.return_value.__enter__.return_value.extract_info.return_value = {}
        path = download_audio("https://youtube.com/shorts/abc123")
        assert path.endswith(".m4a")

    @patch("app.worker.pipeline.download.yt_dlp.YoutubeDL")
    def test_raises_for_private_video(self, mock_ydl_cls: MagicMock) -> None:
        mock_ydl_cls.return_value.__enter__.return_value.extract_info.side_effect = (
            yt_dlp.utils.DownloadError("ERROR: Private video. Sign in if you've been invited.")
        )
        with pytest.raises(PipelineStageError) as exc_info:
            download_audio("https://youtube.com/shorts/private-video")
        assert exc_info.value.stage == "download"
        assert "private" in exc_info.value.human_message.lower()

    @patch("app.core.retry.time.sleep")
    @patch("app.worker.pipeline.download.yt_dlp.YoutubeDL")
    def test_raises_after_retries_exhausted_on_transient_error(
        self, mock_ydl_cls: MagicMock, _mock_sleep: MagicMock
    ) -> None:
        mock_ydl_cls.return_value.__enter__.return_value.extract_info.side_effect = (
            yt_dlp.utils.DownloadError("ERROR: Network unreachable")
        )
        with pytest.raises(PipelineStageError) as exc_info:
            download_audio("https://youtube.com/shorts/flaky")
        assert exc_info.value.stage == "download"


class TestTranscribeAudio:
    @patch("app.worker.pipeline.transcribe._get_model")
    def test_returns_a_transcript(self, mock_get_model: MagicMock) -> None:
        segment = MagicMock(text=" hello world ")
        mock_get_model.return_value.transcribe.return_value = ([segment], MagicMock())
        transcript = transcribe_audio("/tmp/audio.m4a")
        assert transcript == "hello world"

    @patch("app.worker.pipeline.transcribe._get_model")
    def test_raises_when_no_speech_detected(self, mock_get_model: MagicMock) -> None:
        mock_get_model.return_value.transcribe.return_value = ([], MagicMock())
        with pytest.raises(PipelineStageError) as exc_info:
            transcribe_audio("/tmp/no-speech-audio.m4a")
        assert exc_info.value.stage == "transcribe"

    @patch("app.worker.pipeline.transcribe._get_model")
    def test_raises_when_model_errors(self, mock_get_model: MagicMock) -> None:
        mock_get_model.return_value.transcribe.side_effect = RuntimeError("boom")
        with pytest.raises(PipelineStageError) as exc_info:
            transcribe_audio("/tmp/audio.m4a")
        assert exc_info.value.stage == "transcribe"


class TestExtractRecipe:
    @patch("app.worker.pipeline.extract.get_ollama_client")
    def test_returns_a_structured_recipe(self, mock_get_client: MagicMock) -> None:
        mock_get_client.return_value.chat.return_value = _chat_response(_VALID_EXTRACTION_JSON)
        recipe = extract_recipe("some narration about cooking")
        assert recipe.name == "Chicken and Quinoa Bowl"
        assert len(recipe.steps) == 3
        assert len(recipe.ingredients) == 2
        assert recipe.portion_count == 2

    def test_raises_for_empty_transcript(self) -> None:
        with pytest.raises(PipelineStageError) as exc_info:
            extract_recipe("   ")
        assert exc_info.value.stage == "extract"

    @patch("app.worker.pipeline.extract.get_ollama_client")
    def test_raises_when_ollama_unreachable(self, mock_get_client: MagicMock) -> None:
        mock_get_client.return_value.chat.side_effect = ConnectionError("refused")
        with pytest.raises(PipelineStageError) as exc_info:
            extract_recipe("some narration")
        assert exc_info.value.stage == "extract"
        assert "ollama" in exc_info.value.human_message.lower()

    @patch("app.worker.pipeline.extract.get_ollama_client")
    def test_retries_once_on_malformed_json_then_succeeds(self, mock_get_client: MagicMock) -> None:
        mock_get_client.return_value.chat.side_effect = [
            _chat_response("not json"),
            _chat_response(_VALID_EXTRACTION_JSON),
        ]
        recipe = extract_recipe("some narration")
        assert recipe.name == "Chicken and Quinoa Bowl"
        assert mock_get_client.return_value.chat.call_count == 2

    @patch("app.worker.pipeline.extract.get_ollama_client")
    def test_raises_if_still_malformed_after_retry(self, mock_get_client: MagicMock) -> None:
        mock_get_client.return_value.chat.side_effect = [
            _chat_response("not json"),
            _chat_response("still not json"),
        ]
        with pytest.raises(PipelineStageError) as exc_info:
            extract_recipe("some narration")
        assert exc_info.value.stage == "extract"


class TestLookupMacros:
    @patch("app.worker.pipeline.macros.lookup_food_macros")
    def test_recognized_ingredient_is_usda_verified(self, mock_lookup: MagicMock) -> None:
        mock_lookup.return_value = (800.0, 150.0, 0.0, 20.0)
        resolved = lookup_macros(
            [
                ExtractedIngredient(
                    raw_text="2lbs chicken breast", name="chicken breast", quantity=2, unit="lbs"
                )
            ]
        )
        assert resolved[0].macro_source == MacroSource.USDA_VERIFIED
        assert resolved[0].calories == 800.0

    @patch("app.worker.pipeline.macros.get_ollama_client")
    @patch("app.worker.pipeline.macros.lookup_food_macros")
    def test_unrecognized_ingredient_falls_back_to_llm_estimate(
        self, mock_lookup: MagicMock, mock_get_client: MagicMock
    ) -> None:
        mock_lookup.return_value = None
        mock_get_client.return_value.chat.return_value = _chat_response(
            json.dumps({"calories": 5.0, "protein_g": 0.0, "carbs_g": 1.0, "fat_g": 0.0})
        )
        resolved = lookup_macros(
            [
                ExtractedIngredient(
                    raw_text="1 tsp fairy dust", name="fairy dust", quantity=1, unit="tsp"
                )
            ]
        )
        assert resolved[0].macro_source == MacroSource.LLM_ESTIMATED
        assert resolved[0].calories == 5.0

    @patch("app.worker.pipeline.macros.get_ollama_client")
    @patch("app.worker.pipeline.macros.lookup_food_macros")
    def test_falls_back_to_default_estimate_when_llm_also_fails(
        self, mock_lookup: MagicMock, mock_get_client: MagicMock
    ) -> None:
        mock_lookup.return_value = None
        mock_get_client.return_value.chat.side_effect = ConnectionError("refused")
        resolved = lookup_macros(
            [
                ExtractedIngredient(
                    raw_text="1 tsp fairy dust", name="fairy dust", quantity=1, unit="tsp"
                )
            ]
        )
        assert resolved[0].macro_source == MacroSource.LLM_ESTIMATED
        assert resolved[0].calories == 150.0

    @patch("app.worker.pipeline.macros.lookup_food_macros")
    def test_preserves_ingredient_order(self, mock_lookup: MagicMock) -> None:
        mock_lookup.return_value = (100.0, 1.0, 1.0, 1.0)
        ingredients = [
            ExtractedIngredient(raw_text="a", name="chicken breast", quantity=1, unit=None),
            ExtractedIngredient(raw_text="b", name="quinoa", quantity=1, unit=None),
        ]
        resolved = lookup_macros(ingredients)
        assert [r.ingredient.name for r in resolved] == ["chicken breast", "quinoa"]


class TestUsdaClient:
    @patch("app.core.retry.time.sleep")
    def test_returns_none_on_http_error(self, _mock_sleep: MagicMock) -> None:
        from app.services.usda_client import lookup_food_macros

        with patch("app.services.usda_client.httpx.get", side_effect=httpx.ConnectError("down")):
            assert lookup_food_macros("chicken breast") is None
