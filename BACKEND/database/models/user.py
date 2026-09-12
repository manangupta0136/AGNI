"""
User Authentication & Identity Model for AGNI Air-Gapped Workbench.
Provides secure local credentials, user isolation, and multi-user privacy.
"""

import hashlib
import os
import secrets
from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, utc_now


def hash_password(password: str) -> str:
    """
    Hash a password using PBKDF2-HMAC-SHA256 with a cryptographically secure salt.
    Format: salt$hash
    """
    salt = secrets.token_hex(16)
    pw_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000,
    ).hex()
    return f"{salt}${pw_hash}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against stored salt$hash string."""
    try:
        salt, stored_hash = hashed_password.split("$")
        computed_hash = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            100000,
        ).hex()
        return secrets.compare_digest(stored_hash, computed_hash)
    except Exception:
        return False


class User(Base):
    """
    Represents an authenticated local operator or refinery engineer.
    The primary key is username as required for user identification and foreign-key linking.
    """
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        comment="Unique username (Primary Key)",
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Hashed password with salt",
    )
    full_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="Optional display or engineer full name",
    )
    role: Mapped[str] = mapped_column(
        String(32),
        default="engineer",
        nullable=False,
        comment="Role: engineer, auditor, admin",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # User-isolated relationships (Privacy enforcement)
    threads: Mapped[List["Conversation"]] = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    memories: Mapped[List["LongTermMemory"]] = relationship(
        "LongTermMemory",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(username='{self.username}', role='{self.role}')>"
