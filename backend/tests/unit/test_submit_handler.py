import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from bot.handlers.submit import handle_submit


def _make_update(text: str) -> MagicMock:
    update = MagicMock()
    update.effective_chat.id = 42
    update.effective_user.full_name = "Test User"
    update.effective_message.text = text
    return update


def _make_context() -> MagicMock:
    context = MagicMock()
    context.bot.send_message = AsyncMock()
    return context


@patch("bot.handlers.submit.process_recipe_submission")
@patch("bot.handlers.submit.create_pending_recipe")
@patch("bot.handlers.submit.get_or_create_user")
@patch("bot.handlers.submit.SessionLocal")
async def test_queues_a_supported_link(
    mock_session_local: MagicMock,
    mock_get_or_create_user: MagicMock,
    mock_create_pending_recipe: MagicMock,
    mock_task: MagicMock,
) -> None:
    mock_get_or_create_user.return_value = (MagicMock(), False)
    recipe_id = uuid.uuid4()
    mock_create_pending_recipe.return_value = MagicMock(id=recipe_id)
    update = _make_update("https://www.youtube.com/shorts/abc123")
    context = _make_context()

    await handle_submit(update, context)

    mock_task.delay.assert_called_once()
    args, _ = mock_task.delay.call_args
    assert args[0] == str(recipe_id)
    assert args[1] == "https://www.youtube.com/shorts/abc123"
    assert args[3] == "42"

    context.bot.send_message.assert_called_once()
    _, kwargs = context.bot.send_message.call_args
    assert str(recipe_id) in kwargs["text"]


@patch("bot.handlers.submit.process_recipe_submission")
@patch("bot.handlers.submit.SessionLocal")
async def test_ignores_unsupported_text(
    mock_session_local: MagicMock, mock_task: MagicMock
) -> None:
    update = _make_update("hey, how's it going?")
    context = _make_context()

    await handle_submit(update, context)

    mock_task.delay.assert_not_called()
    context.bot.send_message.assert_not_called()
    mock_session_local.assert_not_called()
