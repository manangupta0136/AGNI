"""
Long-Term Memory Model for AGNI Air-Gapped Workbench.
Persists user-specific memory, engineer preferences, plant context, and cross-session instructions.
"""

from typing import Optional
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, generate_uuid, utc_now


class LongTermMemory(Base):
    """
    Stores long-term facts, plant preferences, and contextual memories for each user.
    Enables the AI to remember engineer-specific requirements across multiple sessions.
    """
    __tablename__ = "long_term_memories"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=generate_uuid,
        comment="Unique memory ID",
    )
    username: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("users.username", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign Key linking memory to specific user (Privacy)",
    )
    thread_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Optional source thread where memory was extracted",
    )
    memory_type: Mapped[str] = mapped_column(
        String(64),
        default="preference",
        nullable=False,
        comment="Category: preference, plant_context, engineering_rule, personal_note",
    )
    memory_key: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        comment="Short key/topic (e.g. 'preferred_standard', 'refinery_unit', 'pipe_spec')",
    )
    memory_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Detailed memory content or context fact remembered by AI",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )

    # Relationship back to User
    user: Mapped["User"] = relationship(
        "User",
        back_populates="memories",
    )

    def __repr__(self) -> str:
        return f"<LongTermMemory(user='{self.username}', key='{self.memory_key}', type='{self.memory_type}')>"
