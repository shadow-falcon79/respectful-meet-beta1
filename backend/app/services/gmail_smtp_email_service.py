import html
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings
from app.services.email_service import EmailService


class GmailSmtpEmailService(EmailService):
    """Sends OTP emails via Gmail SMTP using an app password.

    No custom domain or third-party transactional-email account is required.
    Requires a Google account with 2-Step Verification enabled and an App
    Password created for this app (smtp_username / smtp_app_password).
    """

    def send_otp(self, email: str, code: str) -> None:
        if not settings.smtp_username or not settings.smtp_app_password:
            raise RuntimeError("Gmail SMTP is enabled but smtp_username/smtp_app_password are not configured")

        safe_code = html.escape(code)

        message = MIMEMultipart("alternative")
        message["Subject"] = "Your Respectful Meet verification code"
        message["From"] = f"{settings.email_sender_name} <{settings.smtp_username}>"
        message["To"] = email

        text_body = (
            f"Your Respectful Meet verification code is {code}. "
            "It expires in 10 minutes. If you did not request this code, ignore this email."
        )
        html_body = (
            "<div style='font-family:Arial,sans-serif;line-height:1.5'>"
            "<h2>Respectful Meet</h2>"
            "<p>Your verification code is:</p>"
            f"<p style='font-size:28px;font-weight:700;letter-spacing:6px'>{safe_code}</p>"
            "<p>This code expires in 10 minutes.</p>"
            "<p>If you did not request this code, you can safely ignore this email.</p>"
            "</div>"
        )

        message.attach(MIMEText(text_body, "plain"))
        message.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(settings.smtp_username, settings.smtp_app_password)
                server.sendmail(settings.smtp_username, [email], message.as_string())
        except smtplib.SMTPException as exc:
            raise RuntimeError("Gmail SMTP rejected the transactional email") from exc
