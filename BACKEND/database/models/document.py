"""
Confidential Document & RAG Chunk Models for AGNI Air-Gapped Workbench.
Tracks file storage, checksums, vector index states, and text chunk boundaries.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, Text, Boolean, Integer, BigInteger, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, generate_uuid, utc_now


class Document(Base):
    """
    Represents an on-premise confidential technical document uploaded for RAG indexing.
    """
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=generate_uuid,
        comment="Document identifier (e.g. doc-1788629... or UUID)",
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Original filename or technical title",
    )
    username: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("users.username", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Owner username (Foreign Key for user isolation)",
    )
    thread_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Associated thread/chat ID",
    )
    folder_path: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="Folder location containing user PDFs",
    )
    file_path: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="Absolute path on the local air-gapped filesystem",
    )
    file_type: Mapped[str] = mapped_column(
        String(32),
        default="PDF",
        nullable=False,
        comment="MIME or file extension: PDF, DOCX, TXT, PNG, etc.",
    )
    file_size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        nullable=False,
    )
    file_size_str: Mapped[str] = mapped_column(
        String(32),
        default="0 KB",
        nullable=False,
    )
    pages: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        String(64),
        default="Uploaded Document",
        nullable=False,
        index=True,
        comment="Industrial category: Safety & Standards, Inspection Report, etc.",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="uploaded",
        nullable=False,
        index=True,
        comment="Processing status: uploaded, parsing, indexed, failed",
    )
    checksum_sha256: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="Cryptographic SHA-256 hash ensuring document integrity",
    )
    qdrant_collection: Mapped[str] = mapped_column(
        String(64),
        default="mrpl_knowledge_base",
        nullable=False,
        comment="Vector database collection where embeddings are stored",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the document is currently active for RAG context retrieval",
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )
    indexed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="documents",
    )
    chunks: Mapped[List["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentChunk.chunk_index.asc()",
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, title='{self.title}', status='{self.status}')>"


class DocumentChunk(Base):
    """
    Represents an extracted and chunked segment of a Document,
    linked to its Qdrant vector embedding point.
    """
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=generate_uuid,
    )
    document_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Sequential index of the chunk within the document",
    )
    page_number: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Page number where this chunk originated",
    )
    text_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Extracted raw text slice used for semantic similarity search",
    )
    qdrant_point_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="UUID point ID inside Qdrant collection",
    )
    embedding_model: Mapped[Optional[str]] = mapped_column(
        String(64),
        default="bge-m3",
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # Relationship back to Document
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="chunks",
    )

    def __repr__(self) -> str:
        return f"<DocumentChunk(id={self.id}, doc_id={self.document_id}, chunk_idx={self.chunk_index})>"
