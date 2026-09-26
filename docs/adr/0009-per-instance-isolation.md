# 0009: Per-instance isolation as the privacy model

## Status
Accepted

## Context
Multiple unrelated households (e.g. two different families) might want to use this project. Row-level ownership/visibility rules (see [PLAN.md](../../PLAN.md) §2) isolate data *within* a single running instance, but that still requires trusting whoever operates that instance with everyone's data.

## Decision
There is no shared or multi-tenant deployment of this project. Every household runs its own fully independent instance: their own clone of the repo, their own Telegram bot token (via their own BotFather registration), their own database, and their own private network layer (Tailscale) for remote access. Nothing is shared across instances — not infrastructure, not a bot, not a database, not telemetry.

## Rationale
- Application-level isolation (ownership + visibility checks) protects users from each other *within* a shared instance, but doesn't protect them from the instance operator, and makes uptime/privacy dependent on someone else's hardware and administration.
- Physical/infrastructural isolation — a separate instance per household — removes that trust dependency entirely, matching the project's "self-hosted, no data leakage" requirement exactly.
- This is also why the setup process (see [docs/setup.md](../setup.md)) is written as "clone and configure your own instance," not "sign up for an account."

## Consequences
Onboarding a new household costs a few minutes (their own bot token, their own `.env`, their own Tailscale account — all free) rather than being instant, but this is the tradeoff that makes the "no data leakage" guarantee actually true rather than merely application-enforced.
