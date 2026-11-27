from abc import ABC, abstractmethod

from app.core.config import settings


class EmailService(ABC):
    @abstractmethod
    def send_otp(self, email: str, code: str) -> None: ...


class ConsoleEmailService(EmailService):
    """Local-only provider. Never use this in a production environment."""

    def send_otp(self, email: str, code: str) -> None:
        if settings.environment == "production":
            raise RuntimeError("Console OTP delivery is disabled in production")
        print(f"[EmailService:console] OTP generated for {email} (valid 10 minutes)")


def get_email_service() -> EmailService:
    provider = settings.email_provider.lower().strip()
    if provider in ("", "console"):
        return ConsoleEmailService()
    if provider in ("smtp", "gmail_smtp", "gmail"):
        from app.services.gmail_smtp_email_service import GmailSmtpEmailService
        return GmailSmtpEmailService()
    raise RuntimeError(f"Unsupported email provider: {provider}")
