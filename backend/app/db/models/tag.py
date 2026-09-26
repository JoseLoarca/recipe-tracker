"""The ``tags`` table: freeform, deduplicated recipe labels."""

import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Tag(Base):
    """A recipe tag (e.g. "air-fryer-only", "dinner").

    ``name`` is normalized (lowercased, trimmed) on write and kept unique,
    so near-duplicate tags don't proliferate without needing a dedicated
    tag-admin UI.

    Attributes:
        id: Primary key.
        name: The normalized tag text, unique across all tags.
    """

    __tablename__ = "tags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
