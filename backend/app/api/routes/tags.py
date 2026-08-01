"""Listing all known tags, for the frontend's tag filter."""

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import DbSessionDep
from app.db.models.tag import Tag

router = APIRouter(prefix="/api/v1/tags", tags=["tags"])


@router.get("", response_model=list[str])
def list_tags(db: DbSessionDep) -> list[str]:
    """List every known tag name, alphabetically.

    Args:
        db: Database session.

    Returns:
        All distinct tag names.
    """
    tags = db.execute(select(Tag).order_by(Tag.name)).scalars().all()
    return [tag.name for tag in tags]
