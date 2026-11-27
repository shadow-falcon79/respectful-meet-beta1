from pydantic import BaseModel


class AdSessionCreate(BaseModel):
    reward_type: str  # "unlock_messages" | "extra_call_minutes"
    conversation_id: str | None = None


class AdSessionOut(BaseModel):
    session_id: str
    external_ref: str
    reward_type: str
    # Mock-mode only: how long the simulated video should run, in seconds,
    # so the frontend plays a realistic-length rewarded ad.
    mock_duration_seconds: int | None = None

    class Config:
        from_attributes = True


class AdPostbackResult(BaseModel):
    status: str
    reward_type: str | None = None
    bonus_messages: int | None = None
    bonus_call_minutes: int | None = None
