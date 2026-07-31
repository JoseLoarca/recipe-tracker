from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
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
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
