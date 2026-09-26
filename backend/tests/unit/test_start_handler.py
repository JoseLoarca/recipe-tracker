from unittest.mock import AsyncMock, MagicMock, patch

from bot.handlers.start import handle_start


def _make_update() -> MagicMock:
    update = MagicMock()
    update.effective_chat.id = 42
    update.effective_user.full_name = "Test User"
    update.effective_user.username = "testuser"
    return update


def _make_context() -> MagicMock:
    context = MagicMock()
    context.bot.send_message = AsyncMock()
    return context


@patch("bot.handlers.start.get_or_create_user")
@patch("bot.handlers.start.SessionLocal")
async def test_welcomes_a_newly_registered_user(
    mock_session_local: MagicMock, mock_get_or_create_user: MagicMock
) -> None:
    mock_get_or_create_user.return_value = (MagicMock(display_name="Test User"), True)
    update = _make_update()
    context = _make_context()

    await handle_start(update, context)

    _, kwargs = context.bot.send_message.call_args
    assert "Welcome, Test User" in kwargs["text"]
    assert "/create_household" in kwargs["text"]


@patch("bot.handlers.start.get_or_create_user")
@patch("bot.handlers.start.SessionLocal")
async def test_welcomes_back_a_returning_user(
    mock_session_local: MagicMock, mock_get_or_create_user: MagicMock
) -> None:
    mock_get_or_create_user.return_value = (MagicMock(display_name="Test User"), False)
    update = _make_update()
    context = _make_context()

    await handle_start(update, context)

    _, kwargs = context.bot.send_message.call_args
    assert kwargs["text"] == "Welcome back, Test User!"
