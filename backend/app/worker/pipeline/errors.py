"""The exception every pipeline stage raises on failure."""


class PipelineStageError(Exception):
    """A pipeline stage failed, with enough context to log and to explain to the user.

    Attributes:
        stage: Which stage failed (e.g. ``"download"``).
        input_summary: A short description of the input being processed,
            included in logs.
        human_message: A human-readable explanation, suitable for relaying
            back to the user via the Telegram bot (see Milestone 8).
        cause: The underlying exception that triggered this failure, if any.
    """

    def __init__(
        self,
        stage: str,
        input_summary: str,
        human_message: str,
        *,
        cause: BaseException | None = None,
    ) -> None:
        """Initialize the error with its stage, input, and user-facing message."""
        super().__init__(f"[{stage}] {human_message} (input={input_summary!r})")
        self.stage = stage
        self.input_summary = input_summary
        self.human_message = human_message
        self.cause = cause
