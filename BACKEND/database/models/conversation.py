"""
Conversation & Chat Message Models for AGNI Air-Gapped Workbench.
Persists multi-turn conversations, tool invocations, and model latency metrics.
"""

from typing import List, Optional, Any
from datetime import datetime
from sqlalchemy import String, Text, Boolean, Integer, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin, generate_uuid, utc_now


class Conversation(Base, TimestampMixin):
    """
    Represents an ongoing or archived chat session between the operator
    and the AGNI multi-model system.
    """
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=generate_uuid,
        comment="Unique conversation identifier (e.g. chat-xxxx or UUID)",
    )
    title: Mapped[str] = mapped_column(
        String(255),
        default="New Technical Session",
        nullable=False,
        comment="Human-readable title of the chat conversation",
    )
    model_id: Mapped[str] = mapped_column(
        String(64),
        default="engineering-intelligence",
        nullable=False,
        comment="Primary model routing identifier selected by user",
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Flag indicating if conversation has been archived",
    )

    username: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("users.username", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Owner username (Foreign Key to users table for privacy isolation)",
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="threads",
    )
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at.asc()",
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title='{self.title}', model='{self.model_id}')>"


class Message(Base):
    """
    Represents an individual message exchanged within a conversation.
    Captures exact token metrics, specialist model used, and tool executions.
    """
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=generate_uuid,
    )
    conversation_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="'user', 'assistant', or 'system'",
    )
    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full message text content",
    )
    model_used: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="Exact model that produced the answer (e.g. deepseek-r1:1.5b (Coding Specialist))",
    )
    tokens_prompt: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    tokens_completion: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    latency_ms: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="Execution / inference latency in milliseconds",
    )
    tool_calls: Mapped[Optional[Any]] = mapped_column(
        JSON,
        nullable=True,
        comment="Structured payload of tool inputs and outputs (e.g. code sandbox output, vision scans)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )

    # Relationship back to conversation
    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="messages",
    )

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, conv={self.conversation_id}, sender='{self.sender}')>"
