"""Application configuration, loaded from the environment / ``.env``."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All instance-specific configuration, sourced from environment variables.

    See ``.env.example`` at the repo root for the full list with explanations.

    Attributes:
        database_url: SQLAlchemy connection string for Postgres.
        redis_url: Connection string for the Celery broker/result backend.
        ollama_base_url: Where the worker reaches the host-native Ollama
            instance (see docs/adr/0004).
        telegram_bot_token: This instance's bot token, from @BotFather.
        usda_api_key: API key for USDA FoodData Central macro lookups.
        internal_api_key: Shared secret between the bot/worker and the
            backend API, for endpoints the frontend should never call.
        session_cookie_name: Name of the web UI's session cookie.
        session_cookie_secure: Whether the session cookie requires HTTPS.
            Off by default: this stack serves plain HTTP with no TLS
            termination out of the box (see docs/setup.md). Flip to true
            only once you've put HTTPS in front of it (e.g. a reverse
            proxy or Tailscale HTTPS) — otherwise browsers silently drop
            the cookie and login appears broken.
        cors_allowed_origins: Where the frontend is served from, so the
            browser will allow it to call this API with credentials
            (cookies). Comma-separated for more than one origin.
        log_level: Root logger level (e.g. ``"INFO"``, ``"DEBUG"``).
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = (
        "postgresql+psycopg://recipe_tracker:recipe_tracker@postgres:5432/recipe_tracker"
    )
    redis_url: str = "redis://redis:6379/0"
    ollama_base_url: str = "http://host.docker.internal:11434"
    telegram_bot_token: str = ""
    usda_api_key: str = ""
    internal_api_key: str = "change-me"
    session_cookie_name: str = "recipe_tracker_session"
    session_cookie_secure: bool = False
    cors_allowed_origins: str = "http://localhost:8080"
    log_level: str = "INFO"

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        """Parse ``cors_allowed_origins`` into a list for CORSMiddleware.

        Returns:
            The configured origins, split on commas and trimmed.
        """
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide `Settings` instance, loaded once and cached.

    Returns:
        The application settings, populated from the environment.
    """
    return Settings()
