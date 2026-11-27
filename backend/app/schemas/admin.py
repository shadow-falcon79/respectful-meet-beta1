from datetime import date, datetime

from pydantic import BaseModel


class AdminVerifyCodeIn(BaseModel):
    email: str
    code: str


class AdminVerifyCodeOut(BaseModel):
    admin_id: str
    email: str


class VipCreateIn(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    country: str
    city: str
    bio: str | None = None
    interests: list[str] = []


class VipOut(BaseModel):
    user_id: str
    first_name: str
    country: str
    city: str
    photo_url: str | None
    created_at: datetime


class AdminUserOut(BaseModel):
    id: str
    email: str | None
    first_name: str | None
    country: str | None
    is_active: bool
    is_suspended: bool
    role: str
    created_at: datetime


class VipCapacityOut(BaseModel):
    used: int
    capacity: int
    available: int

class AdminPaymentOut(BaseModel):
    id: str
    user_id: str
    plan: str
    stars_amount: int
    status: str
    telegram_user_id: str | None
    telegram_charge_id: str | None
    created_at: datetime


class AdminLikeMatchStatsOut(BaseModel):
    total_likes: int
    likes_today: int
    total_matches: int
    matches_today: int
    match_rate_percent: float

class AdminMessageStatsOut(BaseModel):
    total_messages: int
    messages_today: int
    total_conversations: int
    active_conversations_24h: int

class AdminMessageMetadataOut(BaseModel):
    conversation_id: str
    participant_a_id: str
    participant_b_id: str
    message_count: int
    last_message_at: datetime | None
    last_message_type: str | None

class AdminAnalyticsOut(BaseModel):
    users_total: int
    users_today: int
    active_users_24h: int
    likes_total: int
    matches_total: int
    messages_total: int
    conversations_total: int
    premium_active: int
    payments_successful: int
    revenue_stars: int
    calls_total: int
    call_minutes_total: int

class AdminSubscriptionOut(BaseModel):
    id: str
    user_id: str
    plan: str
    status: str
    started_at: datetime
    expires_at: datetime
    payment_id: str | None

class AdminSettingOut(BaseModel):
    key: str
    value: str
    editable: bool
    description: str

class AdminSettingUpdate(BaseModel):
    value: bool | str
