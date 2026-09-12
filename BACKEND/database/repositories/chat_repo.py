"""
Chat Repository for AGNI Air-Gapped Workbench.
Handles async CRUD operations for conversations, user-isolated threads, and messages.
"""

from typing import List, Optional, Any
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.conversation import Conversation, Message


class ChatRepository:
    """Async repository for conversation threads and message persistence."""

    @staticmethod
    async def get_or_create_conversation(
        session: AsyncSession,
        conversation_id: str,
        title: Optional[str] = None,
        model_id: str = "engineering-intelligence",
        username: Optional[str] = None,
    ) -> Conversation:
        """Fetch existing conversation or create a new one linked to username."""
        clean_user = username.strip().lower() if username else None
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await session.execute(stmt)
        conv = result.scalar_one_or_none()

        if conv is None:
            conv = Conversation(
                id=conversation_id,
                title=title or "New Technical Session",
                model_id=model_id,
                username=clean_user,
            )
            session.add(conv)
            await session.flush()
        else:
            updated = False
            if clean_user and not conv.username:
                conv.username = clean_user
                updated = True
            if title and conv.title == "New Technical Session":
                conv.title = title
                updated = True
            if updated:
                await session.flush()

        return conv

    @staticmethod
    async def get_conversation(
        session: AsyncSession,
        conversation_id: str,
        load_messages: bool = True,
        username: Optional[str] = None,
    ) -> Optional[Conversation]:
        """
        Get single conversation by ID with optional eager loading of messages.
        If username is provided, ensures user isolation (privacy check).
        """
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        if username:
            stmt = stmt.where(Conversation.username == username.strip().lower())
        if load_messages:
            stmt = stmt.options(selectinload(Conversation.messages))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_conversations(
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
        include_archived: bool = False,
    ) -> List[Conversation]:
        """List all conversations ordered by most recent activity."""
        stmt = select(Conversation)
        if not include_archived:
            stmt = stmt.where(Conversation.is_archived.is_(False))
        stmt = stmt.order_by(Conversation.updated_at.desc()).limit(limit).offset(offset)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def list_user_conversations(
        session: AsyncSession,
        username: str,
        limit: int = 50,
        offset: int = 0,
        include_archived: bool = False,
    ) -> List[Conversation]:
        """
        List ONLY conversations belonging to a specific user (Privacy Isolation).
        Ensures User A cannot see User B's threads.
        """
        clean_user = username.strip().lower()
        stmt = select(Conversation).where(Conversation.username == clean_user)
        if not include_archived:
            stmt = stmt.where(Conversation.is_archived.is_(False))
        stmt = stmt.order_by(Conversation.updated_at.desc()).limit(limit).offset(offset)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update_conversation_title(
        session: AsyncSession,
        conversation_id: str,
        new_title: str,
    ) -> Optional[Conversation]:
        """Update conversation title."""
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await session.execute(stmt)
        conv = result.scalar_one_or_none()
        if conv:
            conv.title = new_title
            await session.flush()
        return conv

    @staticmethod
    async def archive_conversation(
        session: AsyncSession,
        conversation_id: str,
        archive: bool = True,
    ) -> bool:
        """Mark a conversation as archived or unarchived."""
        stmt = (
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(is_archived=archive)
        )
        result = await session.execute(stmt)
        return result.rowcount > 0

    @staticmethod
    async def delete_conversation(
        session: AsyncSession,
        conversation_id: str,
    ) -> bool:
        """Delete a conversation and all its messages (cascade)."""
        stmt = delete(Conversation).where(Conversation.id == conversation_id)
        result = await session.execute(stmt)
        return result.rowcount > 0

    @staticmethod
    async def add_message(
        session: AsyncSession,
        conversation_id: str,
        sender: str,
        text: str,
        model_used: Optional[str] = None,
        tokens_prompt: int = 0,
        tokens_completion: int = 0,
        latency_ms: float = 0.0,
        tool_calls: Optional[Any] = None,
        username: Optional[str] = None,
    ) -> Message:
        """
        Record a chat message and automatically link/update the parent conversation.
        """
        # Ensure parent conversation exists and has owner username
        await ChatRepository.get_or_create_conversation(
            session=session,
            conversation_id=conversation_id,
            model_id=model_used or "engineering-intelligence",
            username=username,
        )

        msg = Message(
            conversation_id=conversation_id,
            sender=sender,
            text=text,
            model_used=model_used,
            tokens_prompt=tokens_prompt,
            tokens_completion=tokens_completion,
            latency_ms=latency_ms,
            tool_calls=tool_calls,
        )
        session.add(msg)
        await session.flush()
        return msg

    @staticmethod
    async def get_messages(
        session: AsyncSession,
        conversation_id: str,
        limit: int = 100,
    ) -> List[Message]:
        """Fetch all messages for a conversation ordered chronologically."""
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
