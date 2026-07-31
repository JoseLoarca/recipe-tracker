"""Request/response models for the auth endpoints."""

import uuid

from pydantic import BaseModel


class VerifyCodeRequest(BaseModel):
    """Body of ``POST /api/v1/auth/verify-code``.

    Attributes:
        code: The bot-delivered login code being redeemed.
    """

    code: str


class UserRead(BaseModel):
    """Public representation of a user, returned by the auth endpoints.

    Attributes:
        id: The user's primary key.
        display_name: The user's display name.
    """

    id: uuid.UUID
    display_name: str

    model_config = {"from_attributes": True}
