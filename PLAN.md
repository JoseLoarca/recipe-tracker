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
- **Containerized runtime.** The app (bot, backend, web UI, and any supporting services) runs via Docker/Docker Compose so the user does not need an IDE or dev server running to use it day-to-day — `docker compose up -d` should be sufficient to have everything running persistently in the background.
- **Standalone / reproducible for other users.** Anyone cloning the repo should be able to configure and run their own fully isolated instance:
  - No hardcoded secrets, tokens, or personal data anywhere in the codebase.
  - All instance-specific config (Telegram bot token, USDA API key, database credentials, etc.) supplied via a `.env` file, with a committed `.env.example` documenting every variable.
  - Each instance's data (recipes, users, households) is fully local to that instance — no shared backend, no telemetry, no data ever leaving the runner's own machine/containers.
  - Setup should be scriptable/documented end-to-end: obtaining a Telegram bot token, obtaining a USDA API key, pulling Ollama models, first-run instructions — so a new user can go from clone to working instance by following the README.
- **Automated testing is a first-class requirement, not an afterthought.** Unit tests for core logic from the start (extraction parsing/validation, macro reconciliation logic, visibility/permission rules, shopping list generation, etc.), not just left as a TODO. Coverage expectations and testing strategy should be defined in the implementation plan (what's unit-tested vs. what realistically needs integration/manual testing, e.g. the actual video pipeline).
- **CI pipeline.** GitHub Actions (free for public/personal repos) running tests, linting, and type checks on every push/PR — this is one of the most visible signals to an employer skimming a repo, and costs little to set up.
- **Code quality tooling.** Linting/formatting enforced (e.g. ruff/black or eslint/prettier depending on stack chosen later), type checking (mypy/TypeScript strict mode), and pre-commit hooks so the repo is consistently clean.
- **Repo hygiene expected by reviewers.** A LICENSE file, a clear top-level project structure, meaningful commit history (not one giant commit), and ideally a CONTRIBUTING.md if the project is positioned as open for others to run/extend.
- **Visual proof it works.** Screenshots or a short GIF/demo of the web UI and bot flow in the README — employers skim, they don't always clone and run.
- **Architecture Decision Records (optional but strong signal).** A lightweight `docs/adr/` folder capturing why key choices were made (local-first, Telegram over WhatsApp, USDA cross-check with LLM fallback, etc.) — shows engineering judgment, not just code output.
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
- Single shared Telegram bot instance.
- Each person links their Telegram account to their app user account once, via a one-time linking flow (e.g. a code generated in the web app, entered in the Telegram chat).
- Every recipe has exactly one owning user (whoever sent the link).
- Users may optionally belong to one household (the user + wife's shared household).
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
- Edits are attributed to the owning user; for household-visible recipes, either household member editing behavior needs a simple rule (e.g. only the original owner can edit — confirm in implementation planning).

### 5. Infrastructure & Availability
- All processing (transcription, LLM extraction) runs locally via Ollama and local tools — no paid cloud AI APIs.
- Telegram bot uses long-polling (outbound-only), so the host machine never needs an open inbound port.
- Web UI is reachable from the user's and wife's phones/laptops over a private network layer (e.g. Tailscale), not exposed to the public internet.
- If the host machine is offline, Telegram queues messages server-side; on restart, the bot resumes polling and processes the backlog in order without data loss.

## Open Questions for Implementation Planning
- Exact edit permission rule for household-visible recipes (owner-only vs any household member).
- What happens to a recipe's visibility/ownership if a household is later dissolved or a member leaves (edge case, likely low priority given 2-person scope).
- Whether tags are a fixed taxonomy or freeform/LLM-suggested with user cleanup.
- Retry behavior for failed extractions (manual re-submit only, or automatic retry).

## Success Criteria for MVP
- User can send a YouTube Shorts recipe link via Telegram and, within a reasonable processing time, see a correctly structured recipe (or a clear failure message) in the web UI.
- Wife can do the same independently, with her personal recipes invisible to the user unless shared to Household.
- Both can mark a recipe as Household-visible and see it appear for the other.
- Macros display with a clear verified/estimated label.
- The system survives the host machine being powered off overnight with zero lost submissions.