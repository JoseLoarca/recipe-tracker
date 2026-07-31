from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.db import models  # noqa: F401  (registers models on Base.metadata)
from app.db.base import Base


@pytest.fixture(scope="session")
def engine() -> Generator[Engine]:
    """A real Postgres engine — see CONTRIBUTING.md for starting the DB locally.

    Only creates tables (never drops them) so this is safe to run against the
    same database used for manual `docker compose` testing.
    """
    settings = get_settings()
    test_engine = create_engine(settings.database_url)
    Base.metadata.create_all(test_engine)
    yield test_engine
    test_engine.dispose()


@pytest.fixture
def db_session(engine: Engine) -> Generator[Session]:
    """Wraps each test in an outer transaction (rolled back after) plus a
    self-restarting SAVEPOINT, so service-layer `db.commit()` calls don't
    leak data between tests. See SQLAlchemy's "Joining a Session into an
    External Transaction" recipe.
    """
    connection = engine.connect()
    outer_transaction = connection.begin()
    session = sessionmaker(bind=connection, expire_on_commit=False)()

    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess: Session, transaction: object) -> None:
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    session.close()
    outer_transaction.rollback()
    connection.close()
