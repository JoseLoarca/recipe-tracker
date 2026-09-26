"""Response models for the household endpoint."""

import uuid

from pydantic import BaseModel

from app.schemas.auth import UserRead


class HouseholdRead(BaseModel):
    """A household's public details.

    Attributes:
        id: The household's primary key.
        name: The household's display name.
    """

    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class HouseholdMeRead(BaseModel):
    """Response of ``GET /api/v1/households/me``.

    Attributes:
        household: The current user's household, or None if they haven't
            created or joined one.
        members: The household's members, empty if ``household`` is None.
    """

    household: HouseholdRead | None
    members: list[UserRead]
