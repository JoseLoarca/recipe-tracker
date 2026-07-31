# Recipe Tracker

Turn a YouTube Shorts recipe link into a structured, searchable recipe — ingredients, steps, macros, and a shopping 
list — by sending the link to a Telegram bot. Runs entirely on free, self-hosted infrastructure.

> **Status:** early scaffolding (Milestone 1 of the build plan). Core capture/pipeline features are not yet implemented — see [Roadmap](#roadmap--non-goals) below.

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Screenshots](#screenshots)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Quickstart](#quickstart)
- [Usage](#usage)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Architecture Decision Records](#architecture-decision-records)
- [Roadmap & Non-Goals](#roadmap--non-goals)
- [License](#license)

## Overview

Recipe Tracker was built to solve a specific annoyance: seeing a great whole-food recipe in a short-form video, then 
manually re-typing ingredients, guessing macros, and building a shopping list by hand. 

Instead:

1. Send a YouTube Shorts link to your own Telegram bot.
2. A local pipeline downloads the video, transcribes the narration, and extracts a structured recipe using a local LLM (Ollama) — ingredients, steps, macros per portion, and tags.
3. Ingredient macros are cross-checked against the USDA FoodData Central database (falling back to an LLM estimate when unavailable), with the source clearly labeled.
4. The recipe shows up in a responsive web UI, browsable by tag, with a per-recipe shopping list and an edit form for corrections.

Recipes are private by default. Two people can optionally form a **household** to share select recipes with each other while keeping the rest personal.

**This project is meant to be self-hosted per household** — every family/household runs their own fully independent instance (own clone, own Telegram bot, own database). There is no shared or public instance; see [ADR 0009](docs/adr/0009-per-instance-isolation.md).

## Architecture

See [docs/architecture.md](docs/architecture.md) for a full breakdown of the pipeline and service topology.

## Screenshots

<!-- screenshot: recipe list, mobile + desktop -->
<!-- screenshot: recipe detail with macros and shopping list -->
<!-- gif: telegram submit -> bot ack -> completion message -->

## Tech Stack

| Layer                 | Choice                                                          |
|-----------------------|-----------------------------------------------------------------|
| Backend API           | Python, FastAPI                                                 |
| Background jobs       | Celery + Redis                                                  |
| Bot                   | python-telegram-bot (long-polling)                              |
| Transcription         | faster-whisper                                                  |
| Video download        | yt-dlp                                                          |
| LLM extraction        | Ollama (host-native)                                            |
| Macro data            | USDA FoodData Central API                                       |
| Database              | PostgreSQL + SQLAlchemy + Alembic                               |
| Frontend              | React + Vite + TypeScript                                       |
| Dependency management | [uv](https://github.com/astral-sh/uv) (backend), npm (frontend) |
| Runtime               | Docker Compose                                                  |

## Prerequisites

- Docker and Docker Compose
- [Ollama](https://ollama.com) installed **natively on the host** (not containerized — see [ADR 0004](docs/adr/0004-host-native-ollama.md)), with a model pulled, e.g.:
  ```bash
  ollama pull gemma4:e4b-mlx
  ```
- Your own Telegram bot token from [@BotFather](https://t.me/BotFather) (free)
- Your own USDA FoodData Central API key from [fdc.nal.usda.gov](https://fdc.nal.usda.gov/api-key-signup.html) (free)
- (Optional, for remote mobile access) A free [Tailscale](https://tailscale.com) account

## Quickstart

```bash
cp .env.example .env
# edit .env: set TELEGRAM_BOT_TOKEN, USDA_API_KEY, and a real INTERNAL_API_KEY/POSTGRES_PASSWORD

docker compose up -d
```

Then message your bot on Telegram to register, and follow its prompts to create or join a household.

Full step-by-step walkthrough: [docs/setup.md](docs/setup.md).

## Usage

1. Send a YouTube Shorts link to your bot.
2. The bot acknowledges immediately; processing happens in the background.
3. On completion, the bot replies with a link to the saved recipe in the web UI.
4. Browse, filter by tag, edit, or toggle a recipe's visibility (personal/household) from the web UI.

## Testing

```bash
# Backend
cd backend
uv sync --all-groups
uv run pytest --cov=app

# Frontend
cd frontend
npm ci
npm run test
```

See [PLAN.md](PLAN.md) §8 for the full testing strategy (unit vs. integration vs. manual pipeline QA).

## Project Structure

```
recipe-tracker/
├── backend/    # FastAPI API, Celery worker/pipeline, Telegram bot
├── frontend/   # React + Vite web UI
├── docs/       # architecture, setup guide, ADRs, screenshots
└── docker-compose.yml
```

## Architecture Decision Records

Key technical decisions and their rationale live in [docs/adr/](docs/adr/).

## Roadmap & Non-Goals

Instagram/TikTok support, OCR/visual frame analysis, aggregated shopping lists, and meal planning are explicitly out of 
scope for now — see [PLAN.md](PLAN.md) for the full requirements and non-goals.

## License

See [LICENSE](LICENSE).
