from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator


class PhotoOut(BaseModel):
    id: str
    url: str
    is_primary: bool
    display_order: int

    model_config = {"from_attributes": True}


class ProfileOut(BaseModel):
    user_id: str
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    country: str
    city: str
    bio: str | None
    interests: list[str]
    photos: list[PhotoOut]

    model_config = {"from_attributes": True}


class ProfileUpdateIn(BaseModel):
    # Bounded the same way as registration (see schemas/auth.py). `bio` is
    # a Text column with no DB-level cap, and `interests` is an unbounded
    # array — without limits here, either could be used to bloat storage
    # or send an oversized request body. 2000 chars comfortably covers a
    # real bio; 30 interests of up to 50 chars each comfortably covers real use.
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    gender: str | None = Field(default=None, min_length=1, max_length=50)
    country: str | None = Field(default=None, min_length=1, max_length=100)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    bio: str | None = Field(default=None, max_length=2000)
    interests: list[str] | None = Field(default=None, max_length=30)

    @field_validator("interests")
    @classmethod
    def _interest_items_bounded(cls, value: list[str] | None) -> list[str] | None:
        if value is not None:
            for item in value:
                if len(item) > 50:
                    raise ValueError("Each interest must be at most 50 characters")
        return value
