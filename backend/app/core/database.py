from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# pool_pre_ping avoids serving requests on a dead connection (stale after a
# DB restart/failover). pool_size/max_overflow/pool_recycle are tuned for a
# small-to-medium production instance — raise pool_size if the deployed
# Postgres plan can comfortably hold more concurrent connections per worker.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=max(1, settings.database_pool_size),
    max_overflow=max(0, settings.database_max_overflow),
    pool_recycle=300,
    pool_timeout=20,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models (added from Phase 2 on)."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
