"""Correlation-ID propagation for pipeline logging.

Every log line emitted while processing one recipe submission is tagged
with that submission's correlation ID (and recipe ID), so the full
"received → downloading → ... → saved/failed" journey for one submission
can be found by grepping a single ID, even with many submissions
processing concurrently.
"""

import logging
from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar

_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)
_recipe_id: ContextVar[str | None] = ContextVar("recipe_id", default=None)


@contextmanager
def bind_pipeline_context(*, correlation_id: str, recipe_id: str) -> Generator[None]:
    """Bind a correlation/recipe ID for the duration of a block.

    Args:
        correlation_id: The submission's correlation ID.
        recipe_id: The recipe being processed.

    Yields:
        Nothing; log records emitted within the block are tagged.
    """
    correlation_token = _correlation_id.set(correlation_id)
    recipe_token = _recipe_id.set(recipe_id)
    try:
        yield
    finally:
        _correlation_id.reset(correlation_token)
        _recipe_id.reset(recipe_token)


class PipelineContextFilter(logging.Filter):
    """Attaches the current correlation/recipe ID to every log record.

    Records emitted outside of `bind_pipeline_context` (e.g. from the API
    or bot) get `None` for both fields rather than raising, so this filter
    is safe to install globally.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add ``correlation_id``/``recipe_id`` attributes to a record.

        Args:
            record: The log record being emitted.

        Returns:
            True always — this filter only enriches records, never drops them.
        """
        record.correlation_id = _correlation_id.get()
        record.recipe_id = _recipe_id.get()
        return True
