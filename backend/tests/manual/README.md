# Manual QA Checklist — Video Pipeline

Anything that hits real yt-dlp downloads, real faster-whisper inference, or real Ollama inference is intentionally **not** unit-tested (too slow/nondeterministic for CI). Run this checklist manually before tagging a release, once the pipeline (Milestone 6+) is implemented.

- [ ] Normal case: a typical narrated recipe Short → produces a complete recipe with plausible ingredients/steps/macros.
- [ ] Private video link → bot replies with a clear "private or unavailable" failure message, no partial recipe saved.
- [ ] Region-locked video link → same, region-specific failure message.
- [ ] No-speech / music-only video → bot replies with a "no speech detected" failure message.
- [ ] Non-English audio → confirm behavior (transcribed as-is vs. failure) and document the actual result.
- [ ] Ollama not running on host → bot replies "local AI model unreachable" rather than hanging or crashing the worker.
- [ ] USDA API unreachable (e.g. block the host temporarily) → recipe still saves, with macros marked `llm_estimated` instead of `usda_verified`.
- [ ] Host machine powered off overnight with a pending submission → on restart, the bot processes the backlog and the user still gets a completion/failure message.
