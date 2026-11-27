from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class StartConversationIn(BaseModel):
    to_user_id: str = Field(min_length=1, max_length=36)


class SendMessageIn(BaseModel):
    to_user_id: str = Field(min_length=1, max_length=36)
    ciphertext: str = Field(min_length=1, max_length=20000)
    nonce: str = Field(min_length=16, max_length=64)
    sender_public_key_jwk: str = Field(min_length=1, max_length=4096)
    crypto_version: str = Field(default="v1", pattern=r"^v1$")


class MessageOut(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    type: str
    text: str | None
    ciphertext: str | None = None
    nonce: str | None = None
    sender_public_key_jwk: str | None = None
    crypto_version: str = "v1"
    media_url: str | None = None
    is_read: bool
    created_at: datetime


class ConversationOut(BaseModel):
    id: str
    other_user_id: str
    other_first_name: str
    other_photo_url: str | None
    is_matched: bool
    last_message: str | None
    last_message_at: datetime | None
    unread_count: int
