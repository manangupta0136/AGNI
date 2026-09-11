"""
Security Audit & Code Sandbox Execution Models for AGNI Air-Gapped Workbench.
Guarantees full forensic traceability for air-gap compliance and sandbox runs.
"""

from typing import Optional, Any
from datetime import datetime
from sqlalchemy import String, Text, Integer, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base, generate_uuid, utc_now


class SecurityAuditLog(Base):
    """
    Forensic security audit log recording zero-egress verifications,
    unauthorized network requests, and sensitive system operations.
    """
    __tablename__ = "security_audit_logs"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=generate_uuid,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="egress_check, file_upload, model_switch, sandbox_exec, auth_challenge",
    )
    ip_address: Mapped[str] = mapped_column(
        String(64),
        default="127.0.0.1",
        nullable=False,
    )
    request_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )
    external_connections_detected: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Should ALWAYS be 0 in strict air-gap compliance",
    )
    severity: Mapped[str] = mapped_column(
        String(32),
        default="INFO",
        nullable=False,
        comment="INFO, WARNING, CRITICAL",
    )
    details: Mapped[Optional[Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=True,
        comment="Structured payload detailing the event or network probe output",
    )

    def __repr__(self) -> str:
        return f"<SecurityAuditLog(id={self.id}, event='{self.event_type}', severity='{self.severity}')>"


class CodeExecutionRun(Base):
    """
    Tracks Python code execution runs performed in the isolated local code sandbox.
    Captures stdout, stderr, and execution duration for audit compliance.
    """
    __tablename__ = "code_execution_runs"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=generate_uuid,
    )
    conversation_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    code_snippet: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Code executed in the local sandbox",
    )
    language: Mapped[str] = mapped_column(
        String(32),
        default="python",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="success",
        nullable=False,
        comment="success, error, timeout, blocked",
    )
    stdout: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )
    stderr: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )
    execution_time_ms: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return f"<CodeExecutionRun(id={self.id}, status='{self.status}', time={self.execution_time_ms}ms)>"
