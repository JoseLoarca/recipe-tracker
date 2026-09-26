"""SQLAlchemy engine and session factory for the configured database."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session]:
    """Yield a database session for a single request, closing it afterwards.

    Used as a FastAPI dependency (`app.api.deps.DbSessionDep`); the bot and
    worker instead construct a `SessionLocal()` directly with a ``with``
    block, since they aren't request-scoped.

    Yields:
        A SQLAlchemy `Session` bound to the configured engine.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
