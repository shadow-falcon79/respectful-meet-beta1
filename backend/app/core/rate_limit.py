"""Application-level rate limiting (slowapi / limits).

This is the last line of defense against brute force, credential stuffing
and basic request-flood abuse *within the app process*. It is NOT a
substitute for edge/CDN-level DDoS protection (Cloudflare, AWS
Shield/WAF, etc.) — a high-volume volumetric attack must be absorbed
before it reaches this process. See docs/DDOS_AND_HARDENING.md for the
full defense-in-depth picture.

Storage: in-memory by default (fine for a single backend process). If the
app is ever scaled to multiple processes/instances, set RATE_LIMIT_STORAGE_URL
to a shared Redis URL so limits are enforced across all of them — otherwise
each process gets its own independent quota, which quietly multiplies the
effective limit by the instance count.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.rate_limit_storage_url or "memory://",
    # Generous default so normal browsing/scrolling the feed is never
    # throttled — this exists to stop floods and scripted abuse, not to
    # rate-limit real users.
    default_limits=["300/minute"],
    headers_enabled=True,
)

# Named, stricter limits for the highest-risk endpoints. Applied explicitly
# via @limiter.limit(...) on top of (not instead of) the per-email OTP
# limiter already enforced in app/services/otp_service.py — this one is
# keyed by IP, so it also stops a single attacker from rotating through
# many different email addresses.
AUTH_OTP_REQUEST_LIMIT = "10/minute"  # admin OTP only
AUTH_OTP_VERIFY_LIMIT = "20/minute"  # admin OTP only
AUTH_REGISTER_LIMIT = "10/minute"  # legacy compatibility
PAYMENT_INVOICE_LIMIT = "20/minute"
MESSAGE_SEND_LIMIT = "60/minute"
UPLOAD_LIMIT = "20/minute"
