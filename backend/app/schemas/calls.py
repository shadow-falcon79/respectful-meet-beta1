from pydantic import BaseModel


class CallQuotaOut(BaseModel):
    minutes_remaining_today: int
    can_start_call: bool
