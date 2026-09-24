"""Thin wrapper around the official `ollama` Python client.

Instantiated explicitly with `host=settings.ollama_base_url` rather than
relying on the library's own `OLLAMA_HOST` env var, since our config uses
`OLLAMA_BASE_URL` — an implicit env-var-name coupling would be a subtle
footgun (see PLAN.md's confirmed stack decisions).
"""

from functools import lru_cache

from ollama import Client

from app.config import get_settings


@lru_cache
def get_ollama_client() -> Client:
    """Return a process-wide `ollama.Client`, pointed at the configured host.

    Returns:
        A client for the host-native Ollama instance.
    """
    settings = get_settings()
    return Client(host=settings.ollama_base_url)
