# Architecture

## Overview

```
Telegram user
     │  sends a YouTube Shorts link
     ▼
 Telegram Bot (long-polling, outbound only)
     │  creates a `recipes` row (status=pending) + enqueues a Celery task
     ▼
   Redis (broker)
     │
     ▼
 Celery Worker  ──────────────────────────────────────────────┐
     │  1. download (yt-dlp)                                  │
     │  2. transcribe (faster-whisper)                        │  each stage tagged
     │  3. extract (Ollama, host-native)                      │  with a correlation ID
     │  4. macro lookup (USDA FoodData Central, LLM fallback) │  for end-to-end tracing
     │  5. persist (PostgreSQL)                               │
     └────────────────────────────────────────────────────────┘
     │  on success/failure, notifies the user back through the bot
     ▼
 PostgreSQL  ◄────────────  FastAPI backend  ◄────────────  React web UI (nginx)
```

## Services (docker-compose.yml)

| Service    | Role                                              | Notes                                                 |
|------------|---------------------------------------------------|-------------------------------------------------------|
| `postgres` | Primary datastore                                 | users, households, recipes, ingredients, macros, tags |
| `redis`    | Celery broker/result backend                      |                                                       |
| `backend`  | FastAPI REST API                                  | serves the web UI, runs Alembic migrations on startup |
| `worker`   | Celery worker                                     | runs the video → recipe pipeline                      |
| `bot`      | Telegram bot (long-polling)                       | no inbound ports; outbound HTTPS to Telegram only     |
| `frontend` | React SPA served via nginx                        | talks to `backend` over REST                          |
| Ollama     | **not containerized** — runs natively on the host | see [ADR 0004](adr/0004-host-native-ollama.md)        |

## Identity & data model (summary)

- A person becomes a `user` the first time they message the bot — no signup form, no admin step.
- Users optionally belong to one `household` via an invite code shared by an existing member.
- Every `recipe` has exactly one owner and a `visibility` of `personal` or `household`; visibility rules are enforced in `backend/app/core/visibility.py`.
- Full schema: see [PLAN.md](../PLAN.md) §2.

## Error handling & observability

Every pipeline stage wraps its logic in a `PipelineStageError(stage, input, cause)` and logs structured JSON with a correlation ID that ties every log line for one submission together, from "received" through "saved" or "failed." Failure messages relayed to the user via Telegram are specific and human-readable (e.g. "video is private or region-locked") rather than generic. Full detail: [PLAN.md](../PLAN.md) §4.
