"""
Long-Term Memory Repository for AGNI Air-Gapped Workbench.
Handles storing, querying, and managing engineer-specific long-term memories.
"""

from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.memory import LongTermMemory


class MemoryRepository:
    """Async repository for user-isolated long term memory."""

    @staticmethod
    async def add_memory(
        session: AsyncSession,
        username: str,
        memory_key: str,
        memory_content: str,
        memory_type: str = "preference",
        thread_id: Optional[str] = None,
    ) -> LongTermMemory:
        """Create or update a long-term memory for a user."""
        clean_user = username.strip().lower()
        mem = LongTermMemory(
            username=clean_user,
            thread_id=thread_id,
            memory_type=memory_type,
            memory_key=memory_key,
            memory_content=memory_content,
        )
        session.add(mem)
        await session.flush()
        return mem

    @staticmethod
    async def get_user_memories(
        session: AsyncSession,
        username: str,
        memory_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[LongTermMemory]:
        """Fetch all long-term memories for a specific user."""
        clean_user = username.strip().lower()
        stmt = select(LongTermMemory).where(LongTermMemory.username == clean_user)
        if memory_type:
            stmt = stmt.where(LongTermMemory.memory_type == memory_type)
        stmt = stmt.order_by(LongTermMemory.created_at.desc()).limit(limit)
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def delete_memory(
        session: AsyncSession,
        memory_id: str,
    ) -> bool:
        """Delete a long-term memory record."""
        stmt = delete(LongTermMemory).where(LongTermMemory.id == memory_id)
        res = await session.execute(stmt)
        return res.rowcount > 0
