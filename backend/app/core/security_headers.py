"""Security response headers applied to every request (production hardening).

These headers cost nothing at runtime and close a whole class of client-side
attacks (clickjacking, MIME sniffing, protocol downgrade, leaking referrer
data, unwanted browser feature access). They complement, but do not replace,
edge/CDN-level protection (see docs/DDOS_AND_HARDENING.md).
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Prevent the app from ever being framed (clickjacking).
        response.headers["X-Frame-Options"] = "DENY"
        # Stop browsers from guessing content types away from what the
        # server declared (MIME-sniffing attacks on uploaded media).
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Legacy header; harmless to keep for older browsers/proxies.
        response.headers["X-XSS-Protection"] = "0"
        # Don't leak the full referrer URL (which can contain tokens/paths)
        # to third-party origins.
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Disable powerful browser features the API has no legitimate need for.
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=(), usb=()"
        )
        # Cross-origin isolation hardening for the API responses themselves.
        response.headers["Cross-Origin-Resource-Policy"] = "same-site"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

        # HSTS only makes sense once the site is actually served over HTTPS
        # (which is true in production per validate_production_settings()).
        # Sending it in development would poison browsers pointed at
        # http://localhost.
        if settings.environment.lower() == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )

        # Baseline CSP for the API itself (it serves JSON + /media static
        # files, not HTML app pages, so this stays restrictive). The
        # frontend's own index.html sets its own CSP — see
        # frontend/public/_headers.
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
        )

        return response
