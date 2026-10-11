from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# We pass connect_timeout to prevent long TCP hangs when PostgreSQL server is down
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=settings.DB_POOL_PRE_PING,
    connect_args={"connect_timeout": 3},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for yielding database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> tuple[bool, str]:
    """Safe check of PostgreSQL connectivity with diagnostic status message."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "PostgreSQL database connection verified."
    except Exception as exc:
        # Return safe diagnostic error message without leaking internal database credentials
        error_type = type(exc).__name__
        first_line = str(exc).splitlines()[0] if str(exc).splitlines() else "Connection failed"
        return False, f"PostgreSQL database unavailable ({error_type}): {first_line}"
