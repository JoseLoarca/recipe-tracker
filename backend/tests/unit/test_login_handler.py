from unittest.mock import AsyncMock, MagicMock, patch

from bot.handlers.login import handle_login


def _make_update() -> MagicMock:
    update = MagicMock()
    update.effective_chat.id = 42
    update.effective_user.full_name = "Test User"
    return update


def _make_context() -> MagicMock:
    context = MagicMock()
    context.bot.send_message = AsyncMock()
    return context


@patch("bot.handlers.login.issue_login_code")
@patch("bot.handlers.login.get_or_create_user")
@patch("bot.handlers.login.SessionLocal")
async def test_sends_the_login_code(
    mock_session_local: MagicMock,
    mock_get_or_create_user: MagicMock,
    mock_issue_login_code: MagicMock,
) -> None:
    mock_get_or_create_user.return_value = (MagicMock(), False)
    mock_issue_login_code.return_value = MagicMock(code="123456")
    update = _make_update()
    context = _make_context()

    await handle_login(update, context)

    _, kwargs = context.bot.send_message.call_args
    assert "123456" in kwargs["text"]
