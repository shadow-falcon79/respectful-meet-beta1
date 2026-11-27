from datetime import datetime

from pydantic import BaseModel, Field


class FeedProfileOut(BaseModel):
    user_id: str
    first_name: str
    age: int
    city: str
    country: str
    bio: str | None
    interests: list[str]
    photos: list[str]  # URLs, primary first


class LikeIn(BaseModel):
    to_user_id: str = Field(min_length=1, max_length=36)


class LikeOut(BaseModel):
    id: str
    to_user_id: str
    matched: bool
    created_at: datetime


class MatchOut(BaseModel):
    id: str
    other_user_id: str
    other_first_name: str
    other_photo_url: str | None
    created_at: datetime
