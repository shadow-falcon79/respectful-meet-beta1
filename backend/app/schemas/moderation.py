from datetime import datetime

from pydantic import BaseModel, Field


class BlockIn(BaseModel):
    user_id: str = Field(min_length=1, max_length=36)


class BlockOut(BaseModel):
    id: str
    blocked_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportIn(BaseModel):
    reported_user_id: str = Field(min_length=1, max_length=36)
    reason: str = Field(min_length=1, max_length=100)
    details: str | None = Field(default=None, max_length=2000)
    message_id: str | None = Field(default=None, max_length=36)


class ReportOut(BaseModel):
    id: str
    reported_user_id: str
    reason: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
