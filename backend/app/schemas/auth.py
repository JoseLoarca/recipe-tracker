import uuid

from pydantic import BaseModel


class VerifyCodeRequest(BaseModel):
    code: str


class UserRead(BaseModel):
    id: uuid.UUID
    display_name: str

    model_config = {"from_attributes": True}
