"""
Reference PDF Repository for AGNI Air-Gapped Workbench.
Backs the header -> file location lookup the orchestrator uses to pick which
plant reference document to open (see /api/v1/reference-documents in main.py).
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.reference import PdfDocument


class ReferenceDocumentRepository:
    """Async repository for the pdf_documents header/location index."""

    @staticmethod
    async def list_all(session: AsyncSession) -> List[PdfDocument]:
        """List every reference document (id + header + location)."""
        stmt = select(PdfDocument).order_by(PdfDocument.id.asc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(session: AsyncSession, doc_id: int) -> Optional[PdfDocument]:
        """Fetch a single reference document by its id."""
        stmt = select(PdfDocument).where(PdfDocument.id == doc_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
