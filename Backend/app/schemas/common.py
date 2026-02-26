# app/schemas/common.py
from pydantic import BaseModel, ConfigDict

class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None

    model_config = ConfigDict(from_attributes=True)
