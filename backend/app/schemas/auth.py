from datetime import date

from pydantic import BaseModel, Field, field_validator


class SignUpIn(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date
    gender: str = Field(min_length=1, max_length=50)
    country: str = Field(min_length=1, max_length=100)
    city: str = Field(min_length=1, max_length=100)
    interests: list[str] = Field(default_factory=list, max_length=50)
    accept_terms: bool = False
    terms_version: str = Field(min_length=1, max_length=20, default="2026-09-01")

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        value = value.strip().lower()
        if not value.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username may contain only letters, numbers, underscores and hyphens")
        return value


class SignInIn(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip().lower()


class UserOut(BaseModel):
    id: str
    username: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None

    model_config = {"from_attributes": True}


# Kept for the separate admin OTP flow. Regular user authentication no longer
# uses these models/endpoints.
class RequestCodeIn(BaseModel):
    email: str


class RequestCodeOut(BaseModel):
    message: str = "If this email is valid, a verification code has been sent."


class VerifyCodeIn(BaseModel):
    email: str
    code: str

    @field_validator("code")
    @classmethod
    def code_must_be_six_digits(cls, value: str) -> str:
        if not value.isdigit() or len(value) != 6:
            raise ValueError("Code must be exactly 6 digits")
        return value


class VerifyCodeOut(BaseModel):
    account_exists: bool
    verification_ticket: str


class RegisterIn(BaseModel):
    verification_ticket: str = Field(min_length=1, max_length=4096)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date
    gender: str = Field(min_length=1, max_length=50)
    country: str = Field(min_length=1, max_length=100)
    city: str = Field(min_length=1, max_length=100)
    interests: list[str] = Field(default_factory=list, max_length=50)
    accept_terms: bool = False
    terms_version: str = Field(min_length=1, max_length=20, default="2026-09-01")
