"""Abstract file storage.

Development uses local disk; production/Beta 1 uses the configured S3-compatible
storage through the same interface, so routes and services remain storage-agnostic.
"""

import mimetypes
import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from app.core.config import settings

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE_BYTES = 8 * 1024 * 1024  # 8 MB


class StorageValidationError(Exception):
    pass


class StorageService(ABC):
    @abstractmethod
    def save(self, content: bytes, content_type: str, folder: str) -> str:
        """Validates and saves a file, returns a storage_key."""

    @abstractmethod
    def delete(self, storage_key: str) -> None: ...

    @abstractmethod
    def url_for(self, storage_key: str) -> str: ...


def _validate_image(content: bytes, content_type: str) -> None:
    # Never trust the filename or the client-declared content_type alone —
    # check the actual byte signature (magic bytes) of common image formats.
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise StorageValidationError(f"Unsupported content type: {content_type}")
    if len(content) > MAX_IMAGE_SIZE_BYTES:
        raise StorageValidationError("File too large (max 8MB)")

    signatures: dict[str, bytes] = {
        "image/jpeg": b"\xff\xd8\xff",
        "image/png": b"\x89PNG\r\n\x1a\n",
        "image/webp": b"RIFF",  # followed by "WEBP" at offset 8, checked below
    }
    expected = signatures[content_type]
    if not content.startswith(expected):
        raise StorageValidationError("File content does not match declared type")
    if content_type == "image/webp" and content[8:12] != b"WEBP":
        raise StorageValidationError("File content does not match declared type")


class LocalStorageService(StorageService):
    def __init__(self, base_dir: str | None = None):
        self.base_dir = Path(base_dir or settings.storage_local_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, content: bytes, content_type: str, folder: str) -> str:
        _validate_image(content, content_type)

        ext = mimetypes.guess_extension(content_type) or ""
        # Never trust a client-supplied filename — generate our own.
        safe_name = f"{uuid.uuid4()}{ext}"
        folder_path = self.base_dir / folder
        folder_path.mkdir(parents=True, exist_ok=True)

        target = folder_path / safe_name
        with open(target, "wb") as f:
            f.write(content)

        return f"{folder}/{safe_name}"

    def delete(self, storage_key: str) -> None:
        target = self.base_dir / storage_key
        if target.exists() and target.is_file():
            os.remove(target)

    def url_for(self, storage_key: str) -> str:
        # Render's local filesystem is ephemeral. Use the deployed public URL
        # when configured instead of leaking the development localhost URL.
        base = settings.storage_public_base_url.rstrip("/")
        if base.startswith("/"):
            # Same-origin media path, proxied by the frontend host.
            return f"{base}/{storage_key}"
        if settings.effective_public_backend_url:
            base = f"{settings.effective_public_backend_url.rstrip('/')}/media"
        return f"{base}/{storage_key}"


class S3StorageService(StorageService):
    """S3-compatible object storage for production (AWS S3, Cloudflare R2, etc.)."""

    def __init__(self):
        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError("boto3 is required for object storage") from exc
        kwargs = {
            "aws_access_key_id": settings.storage_access_key,
            "aws_secret_access_key": settings.storage_secret_key,
            "region_name": settings.storage_region,
        }
        if settings.storage_url:
            kwargs["endpoint_url"] = settings.storage_url
        self.client = boto3.client("s3", **kwargs)
        self.bucket = settings.storage_bucket
        if not self.bucket:
            raise RuntimeError("STORAGE_BUCKET is required for object storage")

    def save(self, content: bytes, content_type: str, folder: str) -> str:
        _validate_image(content, content_type)
        ext = mimetypes.guess_extension(content_type) or ""
        key = f"{folder}/{uuid.uuid4()}{ext}"
        self.client.put_object(Bucket=self.bucket, Key=key, Body=content, ContentType=content_type, CacheControl="private, max-age=3600")
        return key

    def delete(self, storage_key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=storage_key)

    # Bucket kept private: never build a "public" URL directly. Generate a
    # short-lived signed URL instead so a leaked link stops working after
    # SIGNED_URL_EXPIRY_SECONDS, and storage credentials stay server-side.
    SIGNED_URL_EXPIRY_SECONDS = 900  # 15 minutes

    def url_for(self, storage_key: str) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": storage_key},
            ExpiresIn=self.SIGNED_URL_EXPIRY_SECONDS,
        )


def get_storage_service() -> StorageService:
    # Use configured object storage in Beta as well as Production. This keeps
    # uploaded photos/media persistent across container restarts and deploys.
    # Local disk remains the safe fallback for development/tests.
    if settings.storage_url and settings.storage_bucket and settings.storage_access_key and settings.storage_secret_key:
        return S3StorageService()
    return LocalStorageService()
