"""A small manual retry helper for the pipeline's transient stages.

PLAN.md's original retry policy called for Celery's `autoretry_for`, which
wraps a whole `@task` — but each pipeline stage here is a plain function
called in sequence within one task, not a separate task of its own, so
`autoretry_for` has nothing to attach to. This helper gives the same
"max 2 retries, exponential backoff" behavior at the stage level instead
(used by `download` and `macros`, the two stages PLAN.md flags as
transient — see PLAN.md §12 for this deviation).
"""

import logging
import time
from collections.abc import Callable

logger = logging.getLogger(__name__)


def retry_with_backoff[T](
    func: Callable[[], T],
    *,
    max_attempts: int = 3,
    base_delay_seconds: float = 1.0,
    retry_on: type[Exception] | tuple[type[Exception], ...] = Exception,
) -> T:
    """Call `func`, retrying on transient failures with exponential backoff.

    Args:
        func: The zero-argument callable to run.
        max_attempts: Total attempts, including the first (default 3, i.e.
            up to 2 retries).
        base_delay_seconds: Delay before the first retry; doubles each
            subsequent attempt.
        retry_on: Exception type(s) that trigger a retry. Any other
            exception propagates immediately.

    Returns:
        Whatever `func` returns, from its first successful attempt.

    Raises:
        Exception: Whatever `func` raised on its final attempt.
    """
    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except retry_on as exc:
            if attempt == max_attempts:
                raise
            delay = base_delay_seconds * (2 ** (attempt - 1))
            logger.warning(
                "Transient failure, retrying",
                extra={"attempt": attempt, "max_attempts": max_attempts, "error": str(exc)},
            )
            time.sleep(delay)
    raise AssertionError("unreachable")  # pragma: no cover
