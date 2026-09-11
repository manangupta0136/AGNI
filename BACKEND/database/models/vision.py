"""
Vision & Multimodal Inspection Models for AGNI Air-Gapped Workbench.
Stores image scan artifacts, OCR extractions, and industrial defect classifications.
"""

from typing import Optional, Any
from datetime import datetime
from sqlalchemy import String, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base, generate_uuid, utc_now


class VisionAnalysis(Base):
    """
    Represents an on-premise multimodal vision analysis of an engineering diagram,
    P&ID blueprint, or equipment inspection photograph.
    """
    __tablename__ = "vision_analyses"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=generate_uuid,
    )
    session_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="Associated chat session or inspection session ID",
    )
    image_path: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="Local path to uploaded inspection image",
    )
    image_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="SHA-256 hash of the inspected image",
    )
    prompt: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Operator prompt or inspection query",
    )
    scan_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Synthesized inspection findings and technical observations",
    )
    detected_defects: Mapped[Optional[Any]] = mapped_column(
        JSON,
        default=list,
        nullable=True,
        comment="Structured list of detected defects, anomalies, or diagram components",
    )
    model_used: Mapped[str] = mapped_column(
        String(64),
        default="qwen2-vl:7b",
        nullable=False,
        comment="Vision model utilized for inference",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return f"<VisionAnalysis(id={self.id}, session={self.session_id}, model='{self.model_used}')>"
