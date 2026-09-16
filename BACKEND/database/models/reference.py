"""
Reference PDF Index for AGNI Air-Gapped Workbench.
A lightweight header -> on-disk file location index the orchestrator uses to
pick which plant reference document to open, without loading every file's
full content into the model's context up front.
"""

from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class PdfDocument(Base):
    """Maps a human-readable document header to its absolute file path."""
    __tablename__ = "pdf_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    header: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Human-readable title used by the model to pick the right document",
    )
    location: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Absolute path to the underlying PDF on the local filesystem",
    )

    def __repr__(self) -> str:
        return f"<PdfDocument(id={self.id}, header='{self.header}')>"
