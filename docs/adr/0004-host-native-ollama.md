# 0004: Ollama runs host-native, not containerized

## Status
Accepted

## Context
LLM extraction (recipe structuring) runs locally via Ollama for cost and privacy reasons. The primary development/deployment target is macOS.

## Decision
Ollama is a required host prerequisite, installed and run natively on the machine — it is explicitly **not** a Docker Compose service. Backend/worker containers reach it over `host.docker.internal:11434` (or the Linux `host-gateway` equivalent).

## Rationale
- Docker Desktop on macOS runs containers inside a Linux VM with no access to Apple's Metal/GPU acceleration. A containerized Ollama would be forced onto CPU-only inference — dramatically slower than native Ollama, which uses Metal directly.
- This is a deliberate performance-over-"one-command-simplicity" tradeoff: the project isn't quite zero-additional-install for other users, but avoids a several-times slowdown on the most common local dev/deploy target.
- Linux hosts with GPU passthrough configured could containerize Ollama with better results, but that adds setup complexity most users of this project won't need; host-native works uniformly across macOS, Windows, and Linux with one code path.

## Consequences
Documented as an explicit prerequisite in [docs/setup.md](../setup.md), alongside Docker itself, including the `ollama pull <model>` step before first run.
