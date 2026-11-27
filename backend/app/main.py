import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.router import router as api_v1_router
from app.core.config import settings
from app.core.logging_config import configure_logging
from app.core.production import validate_production_settings
from app.core.rate_limit import limiter
from app.core.security_headers import SecurityHeadersMiddleware

configure_logging()
logger = logging.getLogger("respectful_meet")

app = FastAPI(title="Respectful Meet API", version="0.1.0")
validate_production_settings()

# --- Request body size cap --------------------------------------------------
# Defense in depth, not a substitute for a WAF/CDN-level cap (see
# docs/DDOS_AND_HARDENING.md). Nothing in this API legitimately needs more
# than the largest upload we accept (8MB image, see storage_service.py);
# this stops a client from streaming an unbounded body at a JSON endpoint
# before Pydantic validation ever runs.
MAX_REQUEST_BODY_BYTES = 10 * 1024 * 1024  # 10 MB


class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > MAX_REQUEST_BODY_BYTES:
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={"detail": "Request body too large"},
                    )
            except ValueError:
                pass  # malformed header — let normal request handling reject it
        return await call_next(request)


app.add_middleware(MaxBodySizeMiddleware)

# --- Rate limiting (brute force / flood protection) -------------------------
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    logger.warning("rate_limit_exceeded path=%s client=%s", request.url.path, request.client.host if request.client else "?")
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Too many requests. Please slow down and try again shortly."},
        headers={"Retry-After": "60"},
    )


# --- Crash safety: never leak stack traces / never let one bad request ------
# take the whole worker down without a controlled JSON response.
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_exception path=%s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Invalid request data", "errors": exc.errors()},
    )


# --- Host header validation (blocks Host-header injection / cache poisoning)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts_list)

# --- Security headers on every response (HSTS, CSP, X-Frame-Options, ...) --
app.add_middleware(SecurityHeadersMiddleware)

# --- CORS: only the configured frontend origin(s), credentials allowed for
# the session cookie, methods/headers scoped to what the API actually uses.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Telegram-Bot-Api-Secret-Token"],
    max_age=600,
)

# --- Response compression for speed on slower mobile connections -----------
app.add_middleware(GZipMiddleware, minimum_size=1024)

app.include_router(api_v1_router)

# Serves uploaded photos directly for the beta. A production deployment
# with real traffic should front this with a CDN or move to S3-compatible
# storage (StorageService makes that a one-file change) — fine for now.
import os

os.makedirs(settings.storage_local_dir, exist_ok=True)
app.mount("/media", StaticFiles(directory=settings.storage_local_dir), name="media")
