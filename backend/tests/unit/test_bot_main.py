from unittest.mock import MagicMock, patch

from telegram.ext import CommandHandler, MessageHandler

from bot.main import build_application, main


def test_build_application_registers_all_handlers() -> None:
    application = build_application("123:fake-token")

    handlers = application.handlers[0]
    command_handlers = [h for h in handlers if isinstance(h, CommandHandler)]
    message_handlers = [h for h in handlers if isinstance(h, MessageHandler)]

    assert len(command_handlers) == 5
    assert len(message_handlers) == 1


@patch("bot.main.get_settings")
def test_main_warns_and_exits_without_a_bot_token(mock_get_settings: MagicMock) -> None:
    mock_get_settings.return_value.telegram_bot_token = ""

    main()  # should return quietly, not raise


@patch("bot.main.build_application")
@patch("bot.main.get_settings")
def test_main_starts_polling_with_a_bot_token(
    mock_get_settings: MagicMock, mock_build_application: MagicMock
) -> None:
    mock_get_settings.return_value.telegram_bot_token = "123:fake-token"

    main()

    mock_build_application.return_value.run_polling.assert_called_once()
