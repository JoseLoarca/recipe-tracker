"""The shared SQLAlchemy declarative base every model inherits from."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base class; provides the metadata Alembic autogenerates against."""
