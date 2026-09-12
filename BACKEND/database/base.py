"""
AGNI Database Base Module
Defines DeclarativeBase and standard column mixins for SQLAlchemy 2.0.
"""

from datetime import datetime, timezone
import uuid
from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def generate_uuid() -> str:
    """Generate a clean UUID string."""
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Return timezone-aware current UTC time."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base class for all AGNI SQLAlchemy ORM models."""
    pass


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamps to models."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        onupdate=utc_now,
        nullable=False,
    )
