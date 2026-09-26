# 0007: Telegram-first identity — auto-registration, no passwords

## Status
Accepted

## Context
The app has no email/password infrastructure and is used by a small, known set of people per instance (a household). A user needs to exist before they can own recipes, and needs some way to authenticate a web browser session.

## Decision
- A person becomes a `user` automatically the first time they message the bot (their `telegram_chat_id` is their identity) — no admin CLI, no manual account creation.
- Household creation/joining happens entirely through bot conversation (create, or join via invite code).
- The web UI never creates users or households; its only auth mechanism is a bot-delivered one-time login code exchanged for a session cookie, proving "this browser belongs to this already-registered Telegram identity."

## Rationale
- Avoids building and securing password storage, reset flows, and email delivery entirely — meaningful attack surface removed for a hobby project with a small, trusted user base.
- The bot's username is unlisted/private, so auto-registration from any unrecognized chat_id carries low risk in this deployment model (one instance per household, not a public service).
- Reuses one identity-proof mechanism (bot-delivered one-time code) for both the household invite flow and web login, rather than building two separate systems.

## Consequences
If this project were ever exposed as a public multi-tenant service (explicitly out of scope — see [ADR 0009](0009-per-instance-isolation.md)), this auth model would need to be revisited; it assumes the bot is private to one household.
