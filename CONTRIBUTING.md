# Contributing

This started as a personal project, but pull requests are welcome if you're running your own instance and want to improve it.

## Development setup

**Backend**

Some tests touch a real Postgres database (see PLAN.md §8 — DB-backed service logic is treated as fast/deterministic enough to unit-test directly, unlike the video pipeline). Start the database once before running them:

```bash
docker compose up -d postgres redis  # published on 127.0.0.1:55432/56379 to avoid clashing with any local Postgres/Redis

cd backend
uv sync --all-groups
DATABASE_URL="postgresql+psycopg://recipe_tracker:change-me@localhost:55432/recipe_tracker" uv run pytest
uv run ruff check .
uv run black --check .
uv run mypy app bot
```

Adjust the password in `DATABASE_URL` to match whatever's in your `.env`.

**Frontend**
```bash
cd frontend
npm ci
npm run test
npm run lint
npm run typecheck
```

## Before opening a PR

- Run the checks above locally — CI (`.github/workflows/`) runs the same lint/typecheck/test/build steps and must be green.
- Add or update unit tests for any change to `backend/app/core/` or `backend/app/services/` — these are expected to have first-class test coverage (see [PLAN.md](PLAN.md) §8 for what's unit-tested vs. integration vs. manual).
- If you're changing a significant technical decision (stack choice, data model, auth flow), add or update the relevant entry in `docs/adr/`.
- Install pre-commit hooks once: `pre-commit install` (config in `.pre-commit-config.yaml`).

## Project context

See [PLAN.md](PLAN.md) for the full requirements, scope, and implementation plan this project is being built against.
