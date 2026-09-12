"""
Audit Report Model for AGNI Air-Gapped Workbench.
Tracks generated Word (.docx) technical inspection reports and compliance audits.
"""

from typing import Optional, Any
from datetime import datetime
from sqlalchemy import String, BigInteger, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base, generate_uuid, utc_now


class AuditReport(Base):
    """
    Represents an official generated technical compliance audit report (.docx / .pdf).
    """
    __tablename__ = "audit_reports"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=generate_uuid,
        comment="Unique report identifier",
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Title of the report (e.g. MRPL_Technical_Audit_2026)",
    )
    conversation_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Source conversation that generated this report, if applicable",
    )
    document_ids: Mapped[Optional[Any]] = mapped_column(
        JSON,
        default=list,
        nullable=True,
        comment="List of document IDs referenced during report generation",
    )
    report_type: Mapped[str] = mapped_column(
        String(64),
        default="Industrial Inspection Audit",
        nullable=False,
        comment="Classification: OISD-116 Inspection, ASME B31.3 Audit, SOP Review",
    )
    file_path: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="Path to generated report on local disk",
    )
    file_size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="generated",
        nullable=False,
        comment="generated, archived, exported",
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return f"<AuditReport(id={self.id}, title='{self.title}', status='{self.status}')>"
