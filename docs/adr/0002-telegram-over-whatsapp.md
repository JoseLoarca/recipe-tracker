# 0002: Telegram over WhatsApp for the capture channel

## Status
Accepted

## Context
Recipes need to be submitted from a phone or desktop while browsing short-form video, ideally via "share to chat app."

## Decision
Use Telegram's Bot API rather than WhatsApp's Cloud API.

## Rationale
- Telegram bot creation is free and instant via @BotFather, with no business-account approval process.
- Long-polling works with zero inbound network exposure — no public webhook/domain required (see [0004](0004-host-native-ollama.md) for the related host-networking posture).
- WhatsApp's Cloud API requires a Meta Business account and restricts free-tier messaging to a 24-hour window after the user last messaged, plus template approval outside that window — unnecessary friction for a personal project.
- Telegram works identically across mobile and desktop clients, satisfying the cross-platform capture requirement for free.
