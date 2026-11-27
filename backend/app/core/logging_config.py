"""Structured logging setup.

Development keeps plain readable console logs. Production emits one JSON
object per line — this is what lets a log aggregator (CloudWatch, Loki,
Datadog, etc.) actually index and alert on errors instead of scraping
free-text tracebacks.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone

from app.core.config import settings


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging() -> None:
    root = logging.getLogger()
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    if settings.environment.lower() == "production":
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )

    root.addHandler(handler)
    root.setLevel(logging.INFO)

    # Quiet down noisy third-party loggers unless something is actually wrong.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
