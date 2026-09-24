from unittest.mock import AsyncMock, MagicMock, patch

from app.core.exceptions import (
    AlreadyInHouseholdError,
    CodeAlreadyConsumedError,
    CodeExpiredError,
    InvalidCodeError,
)
from bot.handlers.household import (
    handle_create_household,
    handle_invite,
    handle_join_household,
)


def _make_update(args: list[str] | None = None) -> MagicMock:
    update = MagicMock()
    update.effective_chat.id = 42
    update.effective_user.full_name = "Test User"
    return update


def _make_context(args: list[str] | None = None) -> MagicMock:
    context = MagicMock()
    context.bot.send_message = AsyncMock()
    context.args = args or []
    return context


class TestHandleCreateHousehold:
    async def test_requires_a_name_argument(self) -> None:
        update, context = _make_update(), _make_context(args=[])

        await handle_create_household(update, context)

        _, kwargs = context.bot.send_message.call_args
        assert "Usage" in kwargs["text"]

    @patch("bot.handlers.household.create_household")
    @patch("bot.handlers.household.get_or_create_user")
    @patch("bot.handlers.household.SessionLocal")
    async def test_creates_the_household(
        self,
        mock_session_local: MagicMock,
        mock_get_or_create_user: MagicMock,
        mock_create_household: MagicMock,
    ) -> None:
        mock_get_or_create_user.return_value = (MagicMock(), False)
        mock_create_household.return_value = MagicMock(name="The Smiths")
        update, context = _make_update(), _make_context(args=["The", "Smiths"])

        await handle_create_household(update, context)

        mock_create_household.assert_called_once()
        _, kwargs = context.bot.send_message.call_args
        assert "The Smiths" in kwargs["text"]

    @patch("bot.handlers.household.create_household")
    @patch("bot.handlers.household.get_or_create_user")
    @patch("bot.handlers.household.SessionLocal")
    async def test_rejects_a_user_already_in_a_household(
        self,
        mock_session_local: MagicMock,
        mock_get_or_create_user: MagicMock,
        mock_create_household: MagicMock,
    ) -> None:
        mock_get_or_create_user.return_value = (MagicMock(), False)
        mock_create_household.side_effect = AlreadyInHouseholdError("already in one")
        update, context = _make_update(), _make_context(args=["Name"])

        await handle_create_household(update, context)

        _, kwargs = context.bot.send_message.call_args
        assert "already" in kwargs["text"].lower()


class TestHandleJoinHousehold:
    async def test_requires_a_code_argument(self) -> None:
        update, context = _make_update(), _make_context(args=[])

        await handle_join_household(update, context)

        _, kwargs = context.bot.send_message.call_args
        assert "Usage" in kwargs["text"]

    @patch("bot.handlers.household.join_household")
    @patch("bot.handlers.household.get_or_create_user")
    @patch("bot.handlers.household.SessionLocal")
    async def test_joins_with_a_valid_code(
        self,
        mock_session_local: MagicMock,
        mock_get_or_create_user: MagicMock,
        mock_join_household: MagicMock,
    ) -> None:
        mock_get_or_create_user.return_value = (MagicMock(), False)
        update, context = _make_update(), _make_context(args=["ABC123"])

        await handle_join_household(update, context)

        mock_join_household.assert_called_once()
        _, kwargs = context.bot.send_message.call_args
        assert "joined" in kwargs["text"].lower()

    @patch("bot.handlers.household.join_household")
    @patch("bot.handlers.household.get_or_create_user")
    @patch("bot.handlers.household.SessionLocal")
    async def test_rejects_an_unknown_code(
        self,
        mock_session_local: MagicMock,
        mock_get_or_create_user: MagicMock,
        mock_join_household: MagicMock,
    ) -> None:
        mock_get_or_create_user.return_value = (MagicMock(), False)
        mock_join_household.side_effect = InvalidCodeError("nope")
        update, context = _make_update(), _make_context(args=["BAD"])

        await handle_join_household(update, context)

        _, kwargs = context.bot.send_message.call_args
        assert "doesn't exist" in kwargs["text"]

    @patch("bot.handlers.household.join_household")
    @patch("bot.handlers.household.get_or_create_user")
    @patch("bot.handlers.household.SessionLocal")
    async def test_rejects_an_already_consumed_code(
        self,
        mock_session_local: MagicMock,
        mock_get_or_create_user: MagicMock,
        mock_join_household: MagicMock,
    ) -> None:
        mock_get_or_create_user.return_value = (MagicMock(), False)
        mock_join_household.side_effect = CodeAlreadyConsumedError("used")
        update, context = _make_update(), _make_context(args=["USED"])

        await handle_join_household(update, context)

        _, kwargs = context.bot.send_message.call_args
        assert "already used" in kwargs["text"]

    @patch("bot.handlers.household.join_household")
    @patch("bot.handlers.household.get_or_create_user")
    @patch("bot.handlers.household.SessionLocal")
    async def test_rejects_an_expired_code(
        self,
        mock_session_local: MagicMock,
        mock_get_or_create_user: MagicMock,
        mock_join_household: MagicMock,
    ) -> None:
        mock_get_or_create_user.return_value = (MagicMock(), False)
        mock_join_household.side_effect = CodeExpiredError("expired")
        update, context = _make_update(), _make_context(args=["EXPIRED"])

        await handle_join_household(update, context)

        _, kwargs = context.bot.send_message.call_args
        assert "expired" in kwargs["text"]

    @patch("bot.handlers.household.join_household")
    @patch("bot.handlers.household.get_or_create_user")
    @patch("bot.handlers.household.SessionLocal")
    async def test_rejects_a_user_already_in_a_household(
        self,
        mock_session_local: MagicMock,
        mock_get_or_create_user: MagicMock,
        mock_join_household: MagicMock,
    ) -> None:
        mock_get_or_create_user.return_value = (MagicMock(), False)
        mock_join_household.side_effect = AlreadyInHouseholdError("already in one")
        update, context = _make_update(), _make_context(args=["CODE"])

        await handle_join_household(update, context)

        _, kwargs = context.bot.send_message.call_args
        assert "already" in kwargs["text"].lower()


class TestHandleInvite:
    @patch("bot.handlers.household.generate_invite_code")
    @patch("bot.handlers.household.get_or_create_user")
    @patch("bot.handlers.household.SessionLocal")
    async def test_requires_a_household(
        self,
        mock_session_local: MagicMock,
        mock_get_or_create_user: MagicMock,
        mock_generate_invite_code: MagicMock,
    ) -> None:
        mock_get_or_create_user.return_value = (MagicMock(household_membership=None), False)
        update, context = _make_update(), _make_context()

        await handle_invite(update, context)

        mock_generate_invite_code.assert_not_called()
        _, kwargs = context.bot.send_message.call_args
        assert "create or join a household" in kwargs["text"]

    @patch("bot.handlers.household.generate_invite_code")
    @patch("bot.handlers.household.get_or_create_user")
    @patch("bot.handlers.household.SessionLocal")
    async def test_generates_an_invite_code(
        self,
        mock_session_local: MagicMock,
        mock_get_or_create_user: MagicMock,
        mock_generate_invite_code: MagicMock,
    ) -> None:
        user = MagicMock()
        user.household_membership.household_id = "household-1"
        mock_session_local.return_value.__enter__.return_value.get.return_value = MagicMock(
            id="household-1"
        )
        mock_get_or_create_user.return_value = (user, False)
        mock_generate_invite_code.return_value = MagicMock(code="XYZ789")
        update, context = _make_update(), _make_context()

        await handle_invite(update, context)

        _, kwargs = context.bot.send_message.call_args
        assert "XYZ789" in kwargs["text"]
