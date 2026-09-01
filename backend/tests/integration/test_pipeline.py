import uuid
from collections.abc import Generator

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.enums import RecipeStatus
from app.db.models.recipe import Recipe
from app.services.recipe_service import create_pending_recipe
from app.services.user_service import get_or_create_user
from app.worker.tasks import process_recipe_submission


@pytest.fixture
def real_session(engine: Engine) -> Generator[Session]:
    """A plain, actually-committing session.

    Unlike `db_session` (savepoint-wrapped so unit tests can roll back
    freely), the pipeline task opens its own `SessionLocal()` connection
    independent of any test transaction — so exercising it end-to-end
    needs data that's really committed, not just visible within one
    connection's uncommitted transaction. Cleans up everything it wrote
    afterwards.
    """
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def test_pipeline_success_path_persists_the_recipe(real_session: Session) -> None:
    user, _ = get_or_create_user(
        real_session, telegram_chat_id="pipeline-test-1", display_name="Pipeline Tester"
    )
    recipe = create_pending_recipe(
        real_session,
        owner=user,
        source_url="https://youtube.com/shorts/normal-video",
        correlation_id=uuid.uuid4(),
    )
    assert recipe.status == RecipeStatus.PENDING

    try:
        process_recipe_submission(
            recipe_id=str(recipe.id),
            source_url=recipe.source_url,
            correlation_id=str(recipe.correlation_id),
        )

        real_session.expire_all()
        saved = real_session.get(Recipe, recipe.id)
        assert saved is not None
        assert saved.status == RecipeStatus.COMPLETE
        assert saved.name == "Chicken and Quinoa Bowl"
        assert saved.failure_reason is None
        assert len(saved.steps) == 3
        assert len(saved.ingredients) == 2
        assert saved.macros is not None
        assert saved.macros.macro_source == "usda_verified"
        assert {tag.name for tag in saved.tags} == {"dinner", "meal-prep"}
    finally:
        real_session.delete(real_session.get(Recipe, recipe.id))
        real_session.commit()
        real_session.delete(user)
        real_session.commit()


def test_pipeline_failure_path_marks_the_recipe_failed(real_session: Session) -> None:
    user, _ = get_or_create_user(
        real_session, telegram_chat_id="pipeline-test-2", display_name="Pipeline Tester 2"
    )
    recipe = create_pending_recipe(
        real_session,
        owner=user,
        source_url="https://youtube.com/shorts/private-video",
        correlation_id=uuid.uuid4(),
    )

    try:
        process_recipe_submission(
            recipe_id=str(recipe.id),
            source_url=recipe.source_url,
            correlation_id=str(recipe.correlation_id),
        )

        real_session.expire_all()
        saved = real_session.get(Recipe, recipe.id)
        assert saved is not None
        assert saved.status == RecipeStatus.FAILED
        assert saved.failure_reason is not None
        assert "private" in saved.failure_reason.lower()
        # No partial data was ever written for a failed recipe.
        assert saved.name == ""
        assert len(saved.steps) == 0
        assert len(saved.ingredients) == 0
        assert saved.macros is None
    finally:
        real_session.delete(real_session.get(Recipe, recipe.id))
        real_session.commit()
        real_session.delete(user)
        real_session.commit()


def test_pipeline_logs_include_the_correlation_id(
    real_session: Session, caplog: pytest.LogCaptureFixture
) -> None:
    user, _ = get_or_create_user(
        real_session, telegram_chat_id="pipeline-test-3", display_name="Pipeline Tester 3"
    )
    recipe = create_pending_recipe(
        real_session,
        owner=user,
        source_url="https://youtube.com/shorts/normal-video",
        correlation_id=uuid.uuid4(),
    )

    try:
        with caplog.at_level("INFO"):
            process_recipe_submission(
                recipe_id=str(recipe.id),
                source_url=recipe.source_url,
                correlation_id=str(recipe.correlation_id),
            )

        assert any(
            getattr(record, "correlation_id", None) == str(recipe.correlation_id)
            for record in caplog.records
        )
    finally:
        real_session.delete(real_session.get(Recipe, recipe.id))
        real_session.commit()
        real_session.delete(user)
        real_session.commit()
