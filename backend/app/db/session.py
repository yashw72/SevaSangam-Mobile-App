"""
Database connection helpers.

Provides both a synchronous engine (for Alembic migrations and seed scripts)
and an async engine (for the FastAPI app at runtime), along with session dependencies.
"""

from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from app.core.config import settings

# URLs from settings (with backwards-compatible variable names)
SYNC_DATABASE_URL = settings.sync_database_url_resolved
ASYNC_DATABASE_URL = settings.async_database_url

# Synchronous engine + session (used by Alembic migrations, seeds, CLI tools)
sync_engine = create_engine(
    SYNC_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)
SessionLocal = SyncSessionLocal

# Asynchronous engine + session (used by runtime FastAPI endpoints)
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    future=True,
)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides an async SQLAlchemy session.
    Closes the session cleanly after the request completes.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a synchronous SQLAlchemy session
    when sync endpoints or scripts are preferred.
    """
    db = SyncSessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
