from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables / .env.

    Beta 1 keeps all external integrations behind configuration so the same
    codebase can move from beta credentials/infrastructure to final values
    without changing application code.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    @field_validator("database_url")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        value = value.strip()
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+psycopg2://" + value[len(prefix):]
        return value


    environment: str = "development"

    database_url: str = "postgresql+psycopg2://respectful_meet:changeme@localhost:5432/respectful_meet"
    database_pool_size: int = 3
    database_max_overflow: int = 2

    cors_origins: str = "http://localhost:5173"

    secret_key: str = "changeme"

    # Rate limiting backend. Empty = in-memory (fine for one process). Set to
    # a Redis URL (e.g. "redis://localhost:6379/0") once the backend runs as
    # more than one process/instance, so limits are shared across all of them.
    rate_limit_storage_url: str = ""

    # Comma-separated list of hostnames this API is allowed to be served as
    # (Host header allowlist — blocks Host-header injection / cache-poisoning
    # style attacks). Example: "api.respectfulmeet.com".
    allowed_hosts: str = "*"
    # Render supplies this hostname at runtime; include it in the host allowlist.
    render_external_hostname: str = ""
    render_external_url: str = ""

    # Transactional email via SMTP
    email_provider: str = "console"
    email_sender_email: str = ""
    email_sender_name: str = "Respectful Meet"

    # SMTP configuration
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_app_password: str = ""

    # Discovery / profile age filter settings
    min_age: int = 18
    max_age: int = 80

    # Telegram Stars payments
    telegram_bot_token: str = ""
    telegram_bot_username: str = "Respectfulmeetpay_bot"
    telegram_webhook_secret: str = ""
    public_backend_url: str = ""

    # Local file storage (Phase 6+ can add an S3-compatible StorageService
    # instead — nothing outside app/services/storage_service.py needs to change).
    storage_local_dir: str = "storage"
    storage_public_base_url: str = "http://localhost:8000/media"
    storage_url: str = ""
    storage_bucket: str = ""
    storage_access_key: str = ""
    storage_secret_key: str = ""
    storage_region: str = "auto"

    # Optional feature flags. Ads remain disabled until a real provider is configured.
    ads_enabled: bool = False

    # Comma-separated list of emails allowed to become ADMIN via the admin
    # OTP login flow. Real value set only in the owner's .env — never here,
    # never in git (backend master spec, section 19).
    admin_allowed_emails: str = ""

    # Web Push / VAPID
    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_subject: str = "mailto:admin@example.com"

    # Rewarded ads / offerwall (AdMantum or similar). Real postback_secret
    # and provider name come from the provider's dashboard once approved.
    # ads_mock_mode MUST be false in production — it exists only so the ad
    # flow can be built and demoed before the provider account is live.
    ads_provider: str = "mock"
    ads_postback_secret: str = ""
    ads_mock_mode: bool = True

    # Automated photo moderation (nudity/CSAM/violence detection) via a
    # third-party provider (e.g. AWS Rekognition, Hive, Sightengine).
    # Disabled by default for the same reason ads are: the code path is
    # real, but there is no provider account yet. Human review of reported
    # photos (app/api/v1/moderation.py) works regardless of this setting —
    # this only adds automated *pre*-screening at upload time.
    photo_moderation_enabled: bool = False
    photo_moderation_provider: str = "none"
    photo_moderation_api_key: str = ""

    @property
    def effective_public_backend_url(self) -> str:
        return self.public_backend_url.strip() or self.render_external_url.strip()

    @property
    def admin_allowed_emails_list(self) -> list[str]:
        return [e.strip().lower() for e in self.admin_allowed_emails.split(",") if e.strip()]

    @property
    def allowed_hosts_list(self) -> list[str]:
        hosts = [h.strip() for h in self.allowed_hosts.split(",") if h.strip()]
        runtime_host = self.render_external_hostname.strip()
        # On Render, replace the development wildcard with the service hostname.
        if runtime_host:
            hosts = [h for h in hosts if h != "*"]
            hosts.append(runtime_host)
        # Remove duplicates while preserving order.
        return list(dict.fromkeys(hosts))

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
