from pydantic import BaseModel, Field


class CryptoIdentityIn(BaseModel):
    public_key_jwk: str = Field(min_length=1, max_length=4096)
    fingerprint: str = Field(min_length=32, max_length=128)


class CryptoIdentityOut(BaseModel):
    user_id: str
    public_key_jwk: str
    fingerprint: str
    crypto_version: str = "v1"
