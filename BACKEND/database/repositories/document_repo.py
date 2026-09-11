"""
Document Repository for AGNI Air-Gapped Workbench.
Handles async CRUD operations for uploaded confidential documents and RAG chunks.
"""

from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.document import Document, DocumentChunk


class DocumentRepository:
    """Async repository for document metadata and chunk index tracking."""

    @staticmethod
    async def create_document(
        session: AsyncSession,
        id: str,
        title: str,
        file_path: str,
        file_type: str = "PDF",
        file_size_bytes: int = 0,
        file_size_str: str = "0 KB",
        pages: int = 1,
        category: str = "Uploaded Document",
        status: str = "uploaded",
        checksum_sha256: Optional[str] = None,
        qdrant_collection: str = "mrpl_knowledge_base",
        is_active: bool = True,
    ) -> Document:
        """Create and persist a new document entry."""
        doc = Document(
            id=id,
            title=title,
            file_path=file_path,
            file_type=file_type,
            file_size_bytes=file_size_bytes,
            file_size_str=file_size_str,
            pages=pages,
            category=category,
            status=status,
            checksum_sha256=checksum_sha256,
            qdrant_collection=qdrant_collection,
            is_active=is_active,
        )
        session.add(doc)
        await session.flush()
        return doc

    @staticmethod
    async def get_document(
        session: AsyncSession,
        document_id: str,
        load_chunks: bool = False,
    ) -> Optional[Document]:
        """Fetch document by ID with optional chunk loading."""
        stmt = select(Document).where(Document.id == document_id)
        if load_chunks:
            stmt = stmt.options(selectinload(Document.chunks))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_documents(
        session: AsyncSession,
        category: Optional[str] = None,
        active_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Document]:
        """List documents with optional filtering by category or active state."""
        stmt = select(Document)
        if category:
            stmt = stmt.where(Document.category == category)
        if active_only:
            stmt = stmt.where(Document.is_active.is_(True))
        stmt = stmt.order_by(Document.uploaded_at.desc()).limit(limit).offset(offset)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update_status(
        session: AsyncSession,
        document_id: str,
        status: str,
    ) -> Optional[Document]:
        """Update processing status (e.g. parsing, indexed, failed)."""
        stmt = select(Document).where(Document.id == document_id)
        result = await session.execute(stmt)
        doc = result.scalar_one_or_none()
        if doc:
            doc.status = status
            if status == "indexed":
                doc.indexed_at = datetime.now(timezone.utc)
            await session.flush()
        return doc

    @staticmethod
    async def toggle_active(
        session: AsyncSession,
        document_id: str,
        is_active: bool,
    ) -> Optional[Document]:
        """Enable or disable document inclusion in RAG retrieval."""
        stmt = select(Document).where(Document.id == document_id)
        result = await session.execute(stmt)
        doc = result.scalar_one_or_none()
        if doc:
            doc.is_active = is_active
            await session.flush()
        return doc

    @staticmethod
    async def delete_document(
        session: AsyncSession,
        document_id: str,
    ) -> bool:
        """Delete document record and associated chunks (cascade)."""
        stmt = delete(Document).where(Document.id == document_id)
        result = await session.execute(stmt)
        return result.rowcount > 0

    @staticmethod
    async def add_chunks(
        session: AsyncSession,
        document_id: str,
        chunks_data: List[dict],
    ) -> List[DocumentChunk]:
        """
        Batch-insert extracted text chunks for a document.
        chunks_data: list of dicts with keys: chunk_index, page_number, text_content, qdrant_point_id
        """
        chunks = [
            DocumentChunk(
                document_id=document_id,
                chunk_index=c.get("chunk_index", idx),
                page_number=c.get("page_number", 1),
                text_content=c["text_content"],
                qdrant_point_id=c.get("qdrant_point_id"),
                embedding_model=c.get("embedding_model", "bge-m3"),
            )
            for idx, c in enumerate(chunks_data)
        ]
        session.add_all(chunks)
        await session.flush()
        return chunks

    @staticmethod
    async def get_chunks_by_document(
        session: AsyncSession,
        document_id: str,
    ) -> List[DocumentChunk]:
        """Fetch all text chunks belonging to a document."""
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
