from pydantic import BaseModel, Field, field_validator

class UserSettingsOut(BaseModel):
    language: str
    push_notifications: bool
    email_notifications: bool
    marketing_notifications: bool
    show_online_status: bool
    profile_discoverable: bool
    show_age: bool
    show_city: bool
    min_age: int
    max_age: int
    discovery_radius_km: int
    timezone: str

class UserSettingsUpdate(BaseModel):
    language: str | None = None
    push_notifications: bool | None = None
    email_notifications: bool | None = None
    marketing_notifications: bool | None = None
    show_online_status: bool | None = None
    profile_discoverable: bool | None = None
    show_age: bool | None = None
    show_city: bool | None = None
    min_age: int | None = Field(default=None, ge=18, le=100)
    max_age: int | None = Field(default=None, ge=18, le=100)
    discovery_radius_km: int | None = Field(default=None, ge=1, le=5000)
    timezone: str | None = Field(default=None, min_length=1, max_length=80)

    @field_validator("language")
    @classmethod
    def normalize_language(cls, value: str | None) -> str | None:
        if value is None: return value
        value = value.upper()
        allowed = {"EN","FR","ES","PT","AR","DE","IT","RU","ZH","JA","TR"}
        if value not in allowed: raise ValueError("Unsupported language")
        return value
