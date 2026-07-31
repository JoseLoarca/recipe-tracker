# Setup Guide

This walks through spinning up your own fully independent instance. Nothing here is shared with anyone else's deployment — see [ADR 0009](adr/0009-per-instance-isolation.md).

## 1. Prerequisites

- Docker + Docker Compose installed.
- [Ollama](https://ollama.com) installed **on your host machine** (not in Docker):
  ```bash
  ollama pull gemma4:e4b-mlx
  curl http://localhost:11434/api/tags   # sanity check it's running
  ```
- A Telegram bot token:
  1. Open a chat with [@BotFather](https://t.me/BotFather) on Telegram.
  2. Send `/newbot` and follow the prompts.
  3. Copy the token it gives you.
- A USDA FoodData Central API key: sign up free at https://fdc.nal.usda.gov/api-key-signup.html.
- (Optional, for reaching the web UI from your phone away from home) A free [Tailscale](https://tailscale.com) account, installed on your host machine and your phone.

## 2. Configure

```bash
cp .env.example .env
```

Edit `.env`:
- `TELEGRAM_BOT_TOKEN` — from BotFather
- `USDA_API_KEY` — from FoodData Central
- `POSTGRES_PASSWORD` / `INTERNAL_API_KEY` — replace the placeholder values with your own random strings
- `OLLAMA_BASE_URL` — leave as `http://host.docker.internal:11434` on macOS/Windows; on Linux this also usually works via the `extra_hosts` entry already in `docker-compose.yml`, but if it doesn't resolve, use your Docker bridge address (commonly `http://172.17.0.1:11434`)

## 3. Run

```bash
docker compose up -d
docker compose ps   # confirm all services are healthy
```

## 4. First-run registration

1. Open a chat with your bot on Telegram and send `/start`.
2. The bot registers you automatically and asks whether to create a new household or join one with an invite code.
3. To share recipes with someone else (e.g. a partner), have them message the same bot and use the invite code you generate with `/invite`.

## 5. Log into the web UI

1. Visit `http://localhost:8080` (or your Tailscale address from another device).
2. Send `/login` to the bot; it DMs you a one-time code.
3. Enter the code on the login page.

## 6. Start tracking recipes

Send any YouTube Shorts link to the bot. It will acknowledge immediately and follow up with a link to the finished recipe once processing completes.
