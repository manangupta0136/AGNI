"""
Database Connection & Session Management for AGNI Air-Gapped Workbench.
Provides async SQLAlchemy 2.0 engine, connection pool, sessionmaker, and FastAPI dependency.
Primary: PostgreSQL via asyncpg. Fallback: SQLite via aiosqlite.
"""

import os
import sys
import logging
from typing import AsyncGenerator, Optional
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text

from database.base import Base
import database.models  # Ensure all models are registered with Base.metadata

logger = logging.getLogger("AGNI.Database")

# Detect default PostgreSQL URL or environment overrides
DEFAULT_POSTGRES_URL = (
    os.getenv("AGNI_DATABASE_URL")
    or os.getenv("DATABASE_URL")
    or "postgresql+asyncpg://nayanprakash@localhost:5432/agni_db"
)

# SQLite fallback path for local offline dev
BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
SQLITE_FALLBACK_URL = f"sqlite+aiosqlite:///{DATA_DIR}/agni_local.db"

# Global references
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None
_active_db_type: str = "unknown"


def _normalize_database_url(url: str) -> str:
    """Ensure asyncpg driver is used for postgresql:// URLs."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def get_engine() -> AsyncEngine:
    """Return the active global AsyncEngine."""
    global _engine
    if _engine is None:
        raise RuntimeError("Database engine has not been initialized. Call init_db() first.")
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the active async session factory."""
    global _session_factory
    if _session_factory is None:
        raise RuntimeError("Database session factory not initialized. Call init_db() first.")
    return _session_factory


async def init_db(database_url: Optional[str] = None) -> AsyncEngine:
    """
    Initialize database engine and create tables if they do not exist.
    Connects to PostgreSQL first; falls back gracefully to SQLite if PostgreSQL is unavailable.
    """
    global _engine, _session_factory, _active_db_type

    primary_url = _normalize_database_url(database_url or DEFAULT_POSTGRES_URL)

    # 1. Attempt connection to primary PostgreSQL
    try:
        logger.info("Connecting to primary PostgreSQL database...")
        engine = create_async_engine(
            primary_url,
            echo=False,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
        )

        # Validate connection with a quick ping
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        
        _engine = engine
        _active_db_type = "postgresql"
        logger.info("Connected to PostgreSQL successfully at: %s", primary_url.split("@")[-1])

    except Exception as pg_exc:
        logger.warning(
            "Primary PostgreSQL connection failed (%s). Attempting local offline SQLite fallback...",
            pg_exc,
        )
        try:
            engine = create_async_engine(
                SQLITE_FALLBACK_URL,
                echo=False,
                pool_pre_ping=True,
            )
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

            _engine = engine
            _active_db_type = "sqlite"
            logger.info("Operating in local SQLite fallback mode at: %s", SQLITE_FALLBACK_URL)
        except Exception as sqlite_exc:
            logger.error("Both PostgreSQL and SQLite fallbacks failed: %s", sqlite_exc)
            raise sqlite_exc

    # Configure sessionmaker
    _session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    # Ensure all tables exist
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database schema verification and table creation complete [%s].", _active_db_type)
    return _engine


async def close_db() -> None:
    """Dispose of the connection pool gracefully on application shutdown."""
    global _engine, _session_factory
    if _engine is not None:
        logger.info("Disposing database connection pool...")
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Database connections closed.")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an AsyncSession per request.
    Automatically handles commit and rollback.
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_db_connection() -> dict:
    """
    Liveness & readiness probe for the database layer.
    Returns database type, connectivity status, and response latency.
    """
    import time

    if _engine is None:
        return {
            "status": "disconnected",
            "active_db": "none",
            "latency_ms": 0.0,
            "error": "Engine not initialized",
        }

    start = time.time()
    try:
        async with _engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            val = result.scalar()
        latency = round((time.time() - start) * 1000, 2)
        return {
            "status": "connected" if val == 1 else "degraded",
            "active_db": _active_db_type,
            "latency_ms": latency,
            "error": None,
        }
    except Exception as exc:
        return {
            "status": "error",
            "active_db": _active_db_type,
            "latency_ms": round((time.time() - start) * 1000, 2),
            "error": str(exc),
        }
