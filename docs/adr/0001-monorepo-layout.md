# 0001: Single monorepo over polyrepo

## Status
Accepted

## Context
The project consists of a backend API, a Celery worker, a Telegram bot, and a React frontend — all built and released together for a solo/2-household hobby project.

## Decision
Keep everything (`backend/`, `frontend/`, `docker-compose.yml`, `docs/`) in one repository.

## Rationale
- Single release cadence: the bot, API, and UI change together and are versioned together.
- Simpler for anyone cloning the repo to self-host — one `git clone` + one `docker compose up` gets the whole stack.
- No cross-repo versioning/dependency-pinning overhead that would only pay off at a scale this project doesn't operate at.
