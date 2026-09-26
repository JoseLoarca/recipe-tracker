import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from bot.notifier import notify_failure, notify_success


def _mock_settings() -> MagicMock:
    settings = MagicMock()
    settings.telegram_bot_token = "test-token"
    settings.frontend_base_url = "http://localhost:8080"
    return settings


class TestNotifySuccess:
    @patch("bot.notifier.get_settings")
    @patch("bot.notifier.Bot")
    def test_sends_a_link_to_the_recipe(
        self, mock_bot_cls: MagicMock, mock_get_settings: MagicMock
    ) -> None:
        mock_get_settings.return_value = _mock_settings()
        mock_bot_cls.return_value.send_message = AsyncMock()
        recipe_id = uuid.uuid4()

        notify_success(chat_id="123", recipe_name="Chicken Bowl", recipe_id=recipe_id)

        _, kwargs = mock_bot_cls.return_value.send_message.call_args
        assert kwargs["chat_id"] == "123"
        assert "Chicken Bowl" in kwargs["text"]
        assert str(recipe_id) in kwargs["text"]

    @patch("bot.notifier.get_settings")
    @patch("bot.notifier.Bot")
    def test_skips_sending_without_a_bot_token(
        self, mock_bot_cls: MagicMock, mock_get_settings: MagicMock
    ) -> None:
        settings = _mock_settings()
        settings.telegram_bot_token = ""
        mock_get_settings.return_value = settings

        notify_success(chat_id="123", recipe_name="Chicken Bowl", recipe_id=uuid.uuid4())

        mock_bot_cls.assert_not_called()


class TestNotifyFailure:
    @patch("bot.notifier.get_settings")
    @patch("bot.notifier.Bot")
    def test_sends_the_failure_reason(
        self, mock_bot_cls: MagicMock, mock_get_settings: MagicMock
    ) -> None:
        mock_get_settings.return_value = _mock_settings()
        mock_bot_cls.return_value.send_message = AsyncMock()

        notify_failure(chat_id="123", failure_reason="This video is private.")

        _, kwargs = mock_bot_cls.return_value.send_message.call_args
        assert kwargs["chat_id"] == "123"
        assert "This video is private." in kwargs["text"]

    @patch("bot.notifier.get_settings")
    @patch("bot.notifier.Bot")
    def test_does_not_raise_if_sending_fails(
        self, mock_bot_cls: MagicMock, mock_get_settings: MagicMock
    ) -> None:
        mock_get_settings.return_value = _mock_settings()
        mock_bot_cls.return_value.send_message = AsyncMock(side_effect=RuntimeError("boom"))

        notify_failure(chat_id="123", failure_reason="oops")
