# 0003: Celery + Redis for the processing pipeline

## Status
Accepted

## Context
Video download, transcription, and LLM extraction are slow (seconds to minutes) and must not block the Telegram bot's reply, and must survive the host machine being powered off and back on.

## Decision
Use Celery with a Redis broker/result backend for the video-processing pipeline, instead of in-process async background tasks.

## Rationale
- Submissions are durably queued in Redis; if the worker process (or the whole machine) restarts, queued jobs are not lost.
- Standard, well-understood retry/backoff semantics (`autoretry_for`) for transient failures (network downloads, USDA API calls) without hand-rolled retry logic.
- Decouples the bot process (must stay responsive to Telegram) from the worker process (CPU/IO-heavy), so one can restart independently of the other.
- Redis is a single lightweight container — minimal added operational cost for the reliability gained over FastAPI `BackgroundTasks` or an in-memory asyncio queue, neither of which survive a process restart.
