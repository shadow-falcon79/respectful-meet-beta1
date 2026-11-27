from datetime import datetime

from pydantic import BaseModel


class PlanOut(BaseModel):
    plan: str
    stars_price: int
    duration_days: int
    call_minutes_per_day: int


class SubscriptionStatusOut(BaseModel):
    is_premium: bool
    plan: str | None
    expires_at: datetime | None
    likes_limit_today: int
    likes_used_today: int
