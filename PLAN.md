# Recipe Tracker — Requirements & Implementation Plan

> Part 1 is the approved requirements/scope. Part 2 (below, after Success Criteria) is the implementation plan. Both evolve as milestones land — this is a living plan, not a frozen spec; the durable record of *why* a decision was made lives in `docs/adr/`.

# Recipe Tracker — Requirements & Scope (Pre-Work)

## Context

The user is pursuing a body-composition goal (low body fat, high muscle %) and relies on whole-food recipes discovered on YouTube Shorts, Instagram Reels, and TikTok. Today, capturing a recipe from a video into something usable (ingredients, steps, macros, shopping list) is manual and annoying. This project automates that capture-and-organize step, running on free/local infrastructure, and is used by both the user and their wife — independently, but with a shared "household" option for recipes they want to see together.

This document defines requirements and MVP scope only. Technical implementation planning (stack, data model, pipeline code) is a separate follow-up step.

## Goals

- Send a video link (YouTube Shorts for MVP) via a chat bot, and get back a structured, saved recipe: name, ingredients (with quantities), steps, macros per portion, tags, and a link back to the source video.
- Browse previously saved recipes on both desktop and mobile.
- Support two people (the user + wife) with fully isolated personal recipes by default, and an optional shared household space for recipes both want visible to each other.
- Run entirely on free infrastructure, locally hosted on the user's personal computer (on 24/7), with no public inbound exposure.
- Tolerate the host machine being offline for periods of time without losing incoming requests.

## Portfolio & Distribution Requirements

This project is intended to be showcased to potential employers, and to be usable by other people who want to run their own instance. These constraints apply from the start, not as later polish:

- **Documentation quality is a first-class deliverable.** README with project overview, architecture diagram/description, setup instructions, and rationale for key technical decisions (why Ollama, why Telegram, why Tailscale, etc.) — written as if a stranger (or a hiring manager) needs to understand and run it with no prior context.
- **Docstrings are non-negotiable.** Every module, class, and function in the backend (`app/`, `bot/`) carries a Google-style docstring (Args/Returns/Raises sections) — enforced via ruff's `pydocstyle` (`D`) rules with `convention = "google"`, not left as a convention people forget. Inline comments stay sparse and explain *why*, not *what* — the docstring requirement is about API-level documentation, not comment density.
- **Containerized runtime.** The app (bot, backend, web UI, and any supporting services) runs via Docker/Docker Compose so the user does not need an IDE or dev server running to use it day-to-day — `docker compose up -d` should be sufficient to have everything running persistently in the background.
- **Standalone / reproducible for other users.** Anyone cloning the repo should be able to configure and run their own fully isolated instance:
  - No hardcoded secrets, tokens, or personal data anywhere in the codebase.
  - All instance-specific config (Telegram bot token, USDA API key, database credentials, etc.) supplied via a `.env` file, with a committed `.env.example` documenting every variable.
  - Each instance's data (recipes, users, households) is fully local to that instance — no shared backend, no telemetry, no data ever leaving the runner's own machine/containers.
  - Setup should be scriptable/documented end-to-end: obtaining a Telegram bot token, obtaining a USDA API key, pulling Ollama models, first-run instructions — so a new user can go from clone to working instance by following the README.
- **Automated testing is a first-class requirement, not an afterthought.** Unit tests for core logic from the start (extraction parsing/validation, macro reconciliation logic, visibility/permission rules, shopping list generation, etc.), not just left as a TODO. Coverage expectations and testing strategy should be defined in the implementation plan (what's unit-tested vs. what realistically needs integration/manual testing, e.g. the actual video pipeline).
- **CI pipeline.** GitHub Actions (free for public/personal repos) running tests, linting, and type checks on every push/PR — this is one of the most visible signals to an employer skimming a repo, and costs little to set up.
- **Code quality tooling.** Linting/formatting enforced (ruff/black for the backend, eslint/prettier for the frontend), type checking (mypy strict / TypeScript strict mode), and pre-commit hooks so the repo is consistently clean.
- **Repo hygiene expected by reviewers.** A LICENSE file, a clear top-level project structure, meaningful commit history (not one giant commit), and a CONTRIBUTING.md since the project is positioned as open for others to run/extend.
- **Visual proof it works.** Screenshots or a short GIF/demo of the web UI and bot flow in the README — employers skim, they don't always clone and run.
- **Architecture Decision Records.** A `docs/adr/` folder capturing why key choices were made (local-first, Telegram over WhatsApp, USDA cross-check with LLM fallback, per-instance isolation, etc.) — shows engineering judgment, not just code output.
- **Robust logging and debuggability is a first-class requirement.** When something fails, there must be a clear trace of what was happening leading up to the failure and a meaningful error message explaining what went wrong — not a silent failure or a generic stack trace.
  - Structured logs per pipeline stage (received → downloading → transcribing → extracting → macro lookup → saved/failed), each tagged with a request/recipe correlation ID so a single submission's full journey can be followed across stages.
  - Errors should be caught at each stage boundary and surfaced with context (which stage, which input, underlying cause) rather than letting raw exceptions bubble up unexplained.
  - Failure messages sent back to the user (via the Telegram bot) should be human-readable and specific (e.g. "couldn't download video — link may be private or region-locked" vs. a generic "something went wrong").
  - Logs persisted (not just console output) so past failures can be inspected after the fact, even if the bot/user already moved on.

## Non-Goals (explicitly out of scope for MVP)

- Instagram Reels and TikTok support (deferred — YouTube Shorts only for MVP).
- OCR of on-screen text overlays and visual/frame-based analysis via local VLM (deferred to v2 — audio transcript only for MVP).
- Aggregated/multi-recipe shopping lists (deferred — per-recipe list only for MVP).
- Support for more than 2 users / households beyond the user + wife (architecture should not preclude it, but no general-purpose multi-tenant onboarding flow is required now).
- Meal planning, scheduling, or calendar features.
- Native mobile app (a responsive web UI is sufficient).

## Functional Requirements

### 1. Capture
- User sends a YouTube Shorts link to a Telegram bot.
- Bot acknowledges receipt immediately (e.g. "queued") and does not block the user while processing happens.
- Processing pipeline downloads the video/audio, transcribes narration, and extracts via local LLM:
  - Recipe name
  - Step-by-step instructions
  - Ingredients with quantities/units
  - Macros per portion (protein/carbs/fat, and calories if derivable)
  - Suggested tags (e.g. cooking method, meal type, diet style)
- Macro extraction cross-checks ingredient/quantity data against the USDA FoodData Central API. If the API is unavailable, fall back to an LLM-estimated macro value, and the recipe record must indicate which method produced the macros (verified vs. estimated).
- Bot replies with a completion message and a link/reference to view the saved recipe once processing finishes.
- If extraction fails (e.g. video unavailable, no speech detected), the bot reports a clear failure reason rather than saving a broken/empty recipe.

### 2. Identity & Access
- Each deployment (Telegram bot + backend + database) is its own fully sandboxed instance — every household/family runs their own separate instance on their own machine, with their own bot token, database, and Tailscale network. There is no shared infrastructure between different families' instances; the same codebase is simply cloned and self-hosted independently by anyone who wants to use it (see Portfolio & Distribution Requirements above).
- Within one instance: a person's first message to the bot auto-registers them as a user (no manual/admin user creation step). The bot then asks them to create a new household or join an existing one via a shareable invite code.
- Every recipe has exactly one owning user (whoever sent the link).
- Users may optionally belong to one household (e.g. the user + wife's shared household).
- Each recipe has a visibility setting: **Personal** (only the owning user sees it) or **Household** (all members of the household see it). Owning user can change this after the fact.
- A user's personal recipes are never visible to anyone else, including household members, unless explicitly shared to Household visibility.

### 3. Browse & View
- Web UI (responsive — usable on both desktop and mobile browsers) lists saved recipes.
- List view is filterable/browsable by tag.
- List view distinguishes (or allows filtering by) "My recipes" vs "Household recipes."
- Recipe detail view shows all extracted fields: name, ingredients, steps, macros (with verified/estimated indicator), tags, and a link back to the original video.
- Detail view includes a per-recipe shopping list (essentially the ingredient list presented as a checklist).

### 4. Editing
- Recipes are editable after extraction — ingredients, steps, tags, and macros can all be manually corrected via an edit form on the detail view.
- Edits are attributed to the owning user; editing stays owner-only regardless of visibility (see §12 decision and docs/adr/0008).

### 5. Infrastructure & Availability
- All processing (transcription, LLM extraction) runs locally via Ollama and local tools — no paid cloud AI APIs.
- Telegram bot uses long-polling (outbound-only), so the host machine never needs an open inbound port.
- Web UI is reachable from the user's and wife's phones/laptops over a private network layer (e.g. Tailscale), not exposed to the public internet.
- If the host machine is offline, Telegram queues messages server-side; on restart, the bot resumes polling and processes the backlog in order without data loss.

## Open Questions for Implementation Planning
- ~~Exact edit permission rule for household-visible recipes~~ — resolved, see §12.
- What happens to a recipe's visibility/ownership if a household is later dissolved or a member leaves (edge case, likely low priority given 2-person scope) — resolved, see §12.
- ~~Whether tags are a fixed taxonomy or freeform/LLM-suggested~~ — resolved, see §12.
- ~~Retry behavior for failed extractions~~ — resolved, see §12.

## Success Criteria for MVP
- User can send a YouTube Shorts recipe link via Telegram and, within a reasonable processing time, see a correctly structured recipe (or a clear failure message) in the web UI.
- Wife can do the same independently, with her personal recipes invisible to the user unless shared to Household.
- Both can mark a recipe as Household-visible and see it appear for the other.
- Macros display with a clear verified/estimated label.
- The system survives the host machine being powered off overnight with zero lost submissions.

---

# Part 2: Implementation Plan

## Confirmed Stack Decisions
- **Backend:** Python 3.14, FastAPI (REST API), python-telegram-bot (long-polling), Celery + Redis (background job queue), faster-whisper (transcription), yt-dlp (download), Ollama (LLM extraction, **host-native, not containerized**), SQLAlchemy + Alembic, PostgreSQL.
- **Ollama client:** the official [`ollama`](https://github.com/ollama/ollama-python) Python library (`from ollama import Client`), not a raw `httpx` call — instantiated explicitly as `Client(host=settings.ollama_base_url)` rather than relying on the library's own `OLLAMA_HOST` env var, since our config uses `OLLAMA_BASE_URL` and an implicit env-var-name coupling would be a subtle footgun. Lands in Milestone 7 (`app/services/ollama_client.py`).
- **Dependency management:** [uv](https://github.com/astral-sh/uv) for the backend — `pyproject.toml` + committed `uv.lock`; Dockerfiles run `uv sync --frozen` for reproducible, fast installs; CI uses `uv` for install/lint/typecheck/test instead of pip/poetry.
- **Frontend:** React + Vite + TypeScript SPA, served via its own Docker container (nginx serving the built static assets).
- **Ollama placement:** Runs natively on the host (required so macOS gets Metal/GPU acceleration — Docker Desktop has no GPU passthrough on macOS, so a containerized Ollama would be CPU-only and much slower). Backend/worker containers reach it via `host.docker.internal:11434` (macOS/Windows) or `extra_hosts: host.docker.internal:host-gateway` (Linux, Docker ≥20.10), configurable via `.env`. Documented as a required host prerequisite alongside Docker itself, including `ollama pull <model>` before first run. Default model: `gemma4:e4b-mlx`.
- **Repo layout:** single monorepo (`backend/`, `frontend/`, `docker-compose.yml`, `docs/adr/`, `README.md`).
- **Deployment model:** each household/family runs their own fully independent instance (own clone, own Telegram bot token via BotFather, own database, own Tailscale network — free tier, up to 3 users/100 devices, covers this use case). No shared infrastructure or cross-instance data path exists anywhere in the design; this is the mechanism that satisfies "no data leakage between users" — isolation is physical/infrastructural, not just row-level.

## 1. Repo Structure
```
recipe-tracker/
├── README.md, CONTRIBUTING.md, LICENSE, .env.example, .pre-commit-config.yaml, docker-compose.yml
├── .github/workflows/{backend-ci.yml, frontend-ci.yml}
├── docs/{architecture.md, setup.md, screenshots/, adr/0001..0009-*.md}
├── backend/
│   ├── pyproject.toml, uv.lock, Dockerfile, Dockerfile.worker, alembic/
│   ├── app/
│   │   ├── main.py, config.py, logging_config.py
│   │   ├── db/{base.py, session.py}, db/models/{user,household,household_membership,household_invite_code,auth_code,session,recipe,recipe_macros,ingredient,step,tag,recipe_tag}.py
│   │   ├── schemas/{auth.py, recipe.py, ingredient.py}, api/deps.py, api/routes/{auth,recipes,tags,households,health}.py
│   │   ├── core/{visibility.py, codes.py, exceptions.py, enums.py, macro_reconciliation.py, shopping_list.py, extraction_schema.py}   # framework-agnostic, unit-tested
│   │   ├── services/{user_service.py, household_service.py, auth_code_service.py, usda_client.py, ollama_client.py}
│   │   └── worker/{celery_app.py, tasks.py, logging_context.py, pipeline/{download,transcribe,extract,macros,persist}.py}
│   ├── bot/{main.py, notifier.py, handlers/{start.py, household.py, login.py, submit.py}}
│   └── tests/{unit/, integration/, manual/README.md}
└── frontend/
    ├── Dockerfile, nginx.conf
    ├── src/{api/, pages/{LoginPage,RecipeListPage,RecipeDetailPage,RecipeEditPage}.tsx, components/{RecipeCard,TagFilterBar,ShoppingList,MacroBadge,VisibilityToggle}.tsx, context/AuthContext.tsx}
    └── tests/unit/
```

## 2. Data Model (PostgreSQL, via SQLAlchemy + Alembic)
| Table | Key Columns | Notes |
|---|---|---|
| `users` | `id`, `display_name`, `telegram_chat_id` (unique, indexed), `created_at` | No password/email — the Telegram chat_id itself *is* the identity, set at auto-registration (first message). One row per person per instance. |
| `households` | `id`, `name`, `created_at` | |
| `household_memberships` | `id`, `user_id` FK, `household_id` FK, unique(`user_id`) | Enforces one household per user without hard-coding "2 users" elsewhere. |
| `household_invite_codes` | `id`, `code` unique, `household_id` FK, `created_by_user_id` FK, `expires_at`, `consumed_by_user_id` nullable | Generated on request via `/invite`; single-use, 24h expiry (more lenient than login codes since it may be shared across a text/call). |
| `auth_codes` | `id`, `code` unique, `user_id` FK, `expires_at`, `consumed_at` nullable | Short-lived (10 min), single-use; bot-delivered one-time code used solely to prove Telegram identity when logging into the web UI. |
| `sessions` | `id`, `user_id` FK, `token` (unique, indexed), `created_at`, `expires_at` | Backs the web session cookie (30-day expiry); an `auth_code` is exchanged for one via `POST /api/v1/auth/verify-code`. |
| `recipes` | `id`, `owner_user_id` FK, `household_id` FK nullable, `visibility` enum(personal/household), `name`, `source_url`, `status` enum(pending/processing/complete/failed), `failure_reason`, `correlation_id` (indexed) | `owner_user_id` never changes; `visibility` is the sole sharing switch. |
| `recipe_macros` | `recipe_id` 1:1, `portion_count`, `calories/protein/carbs/fat_per_portion`, `macro_source` enum(usda_verified/llm_estimated/mixed) | Separate table keeps `recipes` lean; `mixed` covers partial USDA matches. |
| `ingredients` | `id`, `recipe_id` FK, `raw_text`, `name`, `quantity`, `unit`, per-ingredient macros, `macro_source`, `sort_order` | |
| `steps` | `id`, `recipe_id` FK, `step_number`, `text` | |
| `tags` / `recipe_tags` | `tags.name` unique (lowercased) + M2M join | Freeform, normalized on write to avoid near-duplicates. |

Visibility logic lives in `core/visibility.py` (pure, unit-tested functions): `can_view(user, recipe)` — owner always; household member only if `visibility == household`. `can_edit(user, recipe)` — **owner-only** (see §12 decision).

## 3. Docker Compose Services
- `postgres` (postgres:18-alpine, healthcheck, volume, published on `127.0.0.1:55432` for local test runs), `redis` (redis:8-alpine, healthcheck, volume, published on `127.0.0.1:56379`)
- `backend` (FastAPI/uvicorn, runs `alembic upgrade head` on entrypoint, depends_on postgres+redis healthy)
- `worker` (Celery, same image different CMD, `extra_hosts: host.docker.internal:host-gateway`, `OLLAMA_BASE_URL` from `.env`)
- `bot` (python-telegram-bot long-polling, shares backend image, no exposed ports — outbound only)
- `frontend` (multi-stage build → nginx, exposes `8080:80`)
- **Not containerized:** Ollama (host prerequisite, documented in `docs/setup.md`).

## 4. Celery Pipeline (`process_recipe_submission`)
Correlation ID (`uuid4`) generated at message-receipt, stored on the `recipes` row, threaded through every stage via a logging contextvar so all log lines auto-tag `correlation_id` + `recipe_id`.

**Implemented (Milestone 6):** the full task orchestration (download → transcribe → extract → macro lookup → persist), `app/worker/logging_context.py` (contextvar + logging filter), and `app/logging_config.py` writing structured JSON to both stdout and a rotated `backend/logs/pipeline.log`. All four extraction stages are still **mocked** (canned/deterministic outputs) — real yt-dlp/faster-whisper/Ollama/USDA integration is Milestone 7. `persist` is already real, writing through the same models and macro-reconciliation logic as the REST API.

| Stage | Behavior | Error handling |
|---|---|---|
| downloading (`pipeline/download.py`) | yt-dlp fetch + audio extraction | Wrapped in `PipelineStageError(stage, input, cause)`; maps private/region-locked/unavailable to specific human messages. |
| transcribing (`pipeline/transcribe.py`) | faster-whisper | Empty/near-empty transcript = distinct "no speech detected" failure. |
| extracting (`pipeline/extract.py`) | `ollama.Client(host=...).chat(...)` call → validated via `core/extraction_schema.py` (pydantic: name, steps, ingredients, tags) | Unreachable Ollama → "local AI model unreachable — is Ollama running?"; malformed JSON gets one stricter-prompt retry before failing. |
| macro lookup (`pipeline/macros.py`) | USDA FoodData Central per ingredient, `core/macro_reconciliation.py` decides verified/estimated/mixed | USDA timeout/not-found → per-ingredient LLM-estimate fallback; never fails the whole task. |
| persist (`pipeline/persist.py`) | Writes steps/ingredients/macros/tags, sets `status=complete` | On any prior `PipelineStageError`, writes `status=failed` + human `failure_reason` instead — no partial recipes ever saved. |

Retry policy: `autoretry_for` (Celery, max 2, exponential backoff) only on transient stages (download, USDA lookup). Transcription/extraction failures are NOT auto-retried (likely deterministic) — user must resend. Logs are structured JSON, written to a volume-mounted, rotated file (`backend/logs/pipeline.log`) plus stdout.

## 5. Telegram Bot Flow
- **Registration (first contact):** any message from an unrecognized `chat_id` auto-creates a `users` row with that `chat_id` — no manual/admin step, no code needed, since the chat_id itself is the proof of identity for a private, unlisted bot. `/start` immediately asks: "Create a new household, or join one with an invite code?"
  - `/create_household <name>` → creates a `households` row + membership.
  - `/invite` → generates a `household_invite_codes` row to share with a partner (e.g. via text message, outside the app).
  - `/join <code>` → validates the invite code, creates the membership, replies confirming which household they joined.
  - A user can also skip and stay solo (no household) — recipes just default to `personal`.
- **Web login:** `/login` in Telegram → bot generates an `auth_codes` row and DMs the code back → user enters it on the web login page → session cookie issued. This is purely to prove "the browser session belongs to this Telegram identity" — it plays no role in registration or household setup, both of which happen entirely in the bot.
- **Submission (Milestone 8, not yet built):** registered chat sends a URL → bot creates the `recipes` row + enqueues the task with a fresh `correlation_id` → immediate ack ("Queued, ref: ..."). On success, worker calls `bot/notifier.py` to send "Done! `<name>` is ready: `<link>`". On failure, sends the specific human-readable reason.

## 6. FastAPI Backend
**Auth decision:** No passwords, no admin CLI, no separate "linking" step. A person becomes a user simply by messaging the bot (see §5) — the `users.telegram_chat_id` column is set at that moment and never changes. The web UI's *only* job is proving that a given browser session belongs to an already-registered Telegram identity, via a short-lived one-time-code pattern (`auth_codes`, bot-delivered, exchanged for an HttpOnly session cookie backed by the `sessions` table). `Secure` is configurable (`SESSION_COOKIE_SECURE`, default `false`) since the stack serves plain HTTP with no TLS termination out of the box — a hardcoded `Secure` cookie would silently never be sent by real browsers. This avoids all password storage/reset flows and keeps the bot as the single source of truth for identity and household membership; the web UI never creates users or households, only displays/edits data and toggles visibility.

**Implemented so far:** `GET /health`; `POST /api/v1/auth/verify-code`, `POST /api/v1/auth/logout`, `GET /api/v1/auth/me`; `POST /api/v1/recipes`, `GET /api/v1/recipes` (filters: `visibility=mine|household|all`, `tag`, `status`), `GET/PATCH/DELETE /api/v1/recipes/{id}`, `PATCH /api/v1/recipes/{id}/visibility` (owner-only), `GET /api/v1/recipes/{id}/shopping-list`; `GET /api/v1/tags`; `GET /api/v1/households/me`. Recipe creation is a normal authenticated endpoint (not pipeline-only) — manually created recipes are immediately `complete`, since this milestone has no pipeline yet; a recipe's existence is hidden (404, not 403) from users who can't view it, to avoid leaking personal recipes.
**Planned (Milestone 8+):** an internal-only endpoint for pipeline-created pending recipes, protected by a separate `X-Internal-Key` header, used only by the bot/worker, never the frontend.

## 7. Frontend
Routes: `/login` (enter Telegram-delivered code), `/` (list), `/recipes/:id` (detail), `/recipes/:id/edit`. List page filters by tag + mine/household/all. Detail page shows `MacroBadge` (verified/estimated), `ShoppingList` (client-side checkable), source video link, owner-only `VisibilityToggle`. Edit page mirrors the backend validation schema. Plain REST/JSON via a thin fetch client (`credentials: 'include'` for the session cookie); no websockets for MVP — poll or manually refresh while a recipe is pending/processing.

**Implemented (Milestone 5):** all four routes, wrapped in `AuthProvider` + `ProtectedRoute` (redirects to `/login` when the `GET /api/v1/auth/me` check fails). Uses [react-router](https://reactrouter.com) (not `react-router-dom` — as of v7 the DOM bindings live in the base package; `react-router-dom` is a legacy-compatible shim capped at v7, and the vulnerable-version advisory affecting 7.12–8.2 only applies to that shim, not the base package). Backend now runs `CORSMiddleware` (`CORS_ALLOWED_ORIGINS`, credentials allowed) since the frontend and API are different origins — a gap not caught until manual browser testing, since integration tests hit the API directly and never exercise the browser's CORS enforcement.

## 8. Testing Strategy
| Layer | Tooling | Scope |
|---|---|---|
| Unit (backend) | pytest, `backend/tests/unit/` | `core/visibility.py` (owner/household/non-member view+edit matrix), `core/codes.py` (pure, no DB — code format/expiry logic), `auth_code_service.py` and `household_service.py` (expired/consumed/valid code paths, backed by a real Postgres via a per-test SAVEPOINT fixture so service-layer `db.commit()` calls don't leak data across tests), and (once built) `core/macro_reconciliation.py`, `core/shopping_list.py`, `core/extraction_schema.py`. |
| Integration (backend) | pytest + real Postgres test DB | Full registration → household join → login → `/me` → logout chain against the real FastAPI app (implemented); recipe API request/response incl. visibility filtering, and pipeline persist against mocked Ollama/USDA responses (Milestone 4+). |
| Manual (video pipeline) | Documented checklist, `backend/tests/manual/README.md` | Anything hitting real yt-dlp/whisper/Ollama inference is explicitly out of unit-test scope (slow/nondeterministic) — covered by a pre-release checklist (normal video, private video, no-speech video, non-English audio). |
| Frontend | vitest + React Testing Library | `ShoppingList`, `MacroBadge` component behavior. Playwright e2e noted as a deferred stretch goal, not MVP. |

Coverage threshold enforced in CI on `app/core/` and `app/services/` specifically (not I/O-heavy pipeline modules).

## 9. CI (GitHub Actions)
- `backend-ci.yml` (path-filtered to `backend/**`): `uv sync` → lint (`ruff check` — includes `D` pydocstyle rules, `black --check`) → typecheck (mypy) → test (pytest with postgres/redis service containers, coverage upload).
- `frontend-ci.yml` (path-filtered to `frontend/**`): lint (oxlint) → typecheck (`tsc --noEmit` strict) → test (vitest) → build (vite build).

## 10. Documentation Plan
- **README.md:** overview/motivation → architecture diagram → screenshot/GIF placeholders → tech stack table → prerequisites (Docker, host Ollama + pulled model, own Telegram bot token via BotFather, own USDA API key, Tailscale free account) → quickstart (`.env` setup → `docker compose up -d` → message your bot to register → create/join a household → log into the web UI) → usage walkthrough → testing → project structure → ADR index → roadmap/non-goals → license. Explicitly documents that this repo is meant to be **self-hosted per household** — no shared/public instance exists or is intended.
- **docs/adr/:** 0001 monorepo layout; 0002 Telegram over WhatsApp (free bot API, no business-account approval); 0003 Celery+Redis over in-process async (survives restarts/downtime); 0004 host-native Ollama (Metal acceleration, no Docker GPU passthrough on macOS); 0005 USDA-verified-with-LLM-fallback (never the reverse); 0006 Postgres+SQLAlchemy+Alembic; 0007 Telegram-first identity — auto-registration on first bot contact plus bot-delivered one-time codes for web login, no passwords, no admin CLI; 0008 household edit permission defaults to owner-only; 0009 per-instance isolation as the privacy model.

## 11. Recommended Build Sequence (incremental PRs)
1. ✅ Scaffolding: repo structure, `uv`-managed `pyproject.toml`/`uv.lock`, Compose stubs, `/health` endpoint, Vite hello-world, both CI workflows green, pre-commit config.
2. ✅ Data model + Alembic migration + `visibility.py` unit tests against real models.
3. ✅ Bot auto-registration + household create/join (invite codes) + web login-code flow + session cookie, with integration tests covering the full registration→household→login chain.
4. ✅ Recipe CRUD API against seeded/manual data (no pipeline yet) + shopping-list/macro-reconciliation unit tests.
5. ✅ Frontend core pages wired to the real API.
6. ✅ Celery pipeline skeleton with mocked stage bodies, correlation-id logging plumbing proven end-to-end.
7. Real pipeline stages, one PR each: download → transcribe → extract (ollama-python client + schema validation) → USDA macros (+ fallback).
8. End-to-end Telegram submission flow (bot → enqueue → notifier callbacks → human-readable failure copy).
9. Documentation/polish pass: ADRs, README screenshots, architecture diagram, coverage thresholds.
10. Hardening: retry/backoff tuning, log rotation, edge cases (household dissolution, empty transcript, malformed JSON retry).

## 12. Flagged Decisions (resolved)
- **Household edit permission → owner-only**, even for household-visible recipes. The stated need was shared *viewing*, not shared *editing*; allowing any household member to silently edit another's recipe (with no versioning/audit trail in MVP) risks unwanted changes. If mutual editing is wanted later, add it as an explicit opt-in co-edit flag plus an edit history, rather than defaulting to it.
- **Household dissolution/member leaving →** any of that member's recipes marked `household` auto-revert to `personal` (privacy fail-safe); no dedicated UI needed for MVP since household management isn't self-service yet. Not yet implemented — revisit when household management UI exists.
- **Tag taxonomy →** freeform + LLM-suggested, normalized (lowercase/trimmed) on write via a unique constraint; avoids building tag-admin UI while preventing near-duplicate proliferation.
- **Retry behavior →** automatic retry (max 2, backoff) only for transient stages (download, USDA lookup); transcription/extraction failures require manual resend since they're likely deterministic. Documented in README and in the bot's failure-message copy.
- **Session cookie `Secure` flag →** configurable, default `false` (see §6) — a real bug caught during Milestone 3: a hardcoded `Secure` cookie is silently dropped by browsers over plain HTTP, which is what this stack serves by default.
- **SQLAlchemy relationship caching →** a real bug caught during Milestone 4: `household_service.create_household`/`join_household` check `user.household_membership is None` before creating the membership, which lazy-loads (and caches) `None` on that attribute. With `expire_on_commit=False` (needed so the bot/API don't refetch objects after every commit), that stale `None` never refreshes — so creating a household-visible recipe in the same request/session right after joining a household would incorrectly fail. Fixed by explicitly assigning `user.household_membership = membership` in-memory right after creating it, rather than relying on SQLAlchemy to notice.
- **CORS →** a real gap caught during Milestone 5's manual browser verification (not by any automated test, since integration tests call the FastAPI app in-process and never go through an actual browser's CORS enforcement): the frontend and backend are different origins in dev (`:8080` vs `:8000`), and with no `CORSMiddleware` configured, every credentialed fetch from the browser would have silently failed. Fixed by adding `CORSMiddleware` with `CORS_ALLOWED_ORIGINS` (credentials allowed) — worth remembering that backend integration tests can't catch browser-enforced policies like CORS or cookie `SameSite`/`Secure` behavior; those need an actual browser pass.
- **Flexbox + `select { width: 100% }` →** a real CSS bug caught during the same manual pass: a `<select>` with `width: 100%` and `flex-basis: auto` inside a flex row resolves its flex-basis from that 100% width, so it claims the entire row and squeezes sibling flex items (an ingredient text input) down to ~0. Fixed by not defaulting `<select>` to full width globally — only `input`/`textarea` get that default, with per-context overrides for tag-filter/ingredient-row selects.
- **`logger.info(..., extra={"name": ...})` →** a real bug caught during Milestone 6: `name` is a reserved `LogRecord` attribute (the logger's own name), so passing it in `extra` raises inside `makeRecord` — but only once the root logger's level actually permits the record to be built. It stayed invisible while no test had raised the log level past the default `WARNING`, then broke the instant a test imported the worker and triggered `configure_logging()`. Fixed by renaming the key (`ingredient_name`); the whole `extra` dict in every pipeline stage was then audited for other collisions with reserved `LogRecord` attributes (`name`, `msg`, `args`, `levelname`, `pathname`, `lineno`, `funcName`, `created`, `thread`, `process`, etc.) — none of the others collided.
- **Celery hijacks the root logger →** a real gap caught during Milestone 6's manual worker-dispatch test (not any automated test — calling the task function directly, as tests do, never goes through Celery's own `Worker` bootstep sequence): by default, Celery's `worker` command installs its own logging handlers on startup, silently overriding whatever `configure_logging()` set up — every pipeline log line lost its JSON structure and its correlation ID the moment a task ran inside a real `celery worker` process, even though everything looked correct when tested via a direct function call. Fixed with `celery_app.conf.worker_hijack_root_logger = False`. Reinforces the same lesson as the CORS gap in Milestone 5: some classes of bugs only exist in the real runtime (a browser, an actual `celery worker` process) and are invisible to tests that call code in-process.

## Verification
- `docker compose up -d` brings up postgres/redis/backend/worker/bot/frontend cleanly with all healthchecks green (Ollama running natively beforehand).
- CI green on a fresh PR (lint incl. docstrings, typecheck, unit+integration tests, frontend build) before merging each milestone in §11.
- Manual pipeline checklist (backend/tests/manual/README.md) run against a handful of real YouTube Shorts links covering the normal/edge cases before considering the pipeline "done."
- End-to-end manual check: message the bot to auto-register → create a household → invite a second test account and have it join via code → submit a real Shorts link → receive queued ack → receive completion message → recipe visible in web UI with correct macros/verified-estimated label → shopping list renders → visibility toggle and household view work correctly between the two test users.
- Cross-instance isolation sanity check: spin up a second, fully separate instance (own `.env`, own bot token, own containers) and confirm there is no code path or shared resource connecting it to the first instance — this is what backs the "no data leakage between households" guarantee.
