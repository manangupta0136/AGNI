"""
User Repository for AGNI Air-Gapped Workbench.
Handles user registration, authentication, credential validation, and user profile queries.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user import User, hash_password, verify_password


class UserRepository:
    """Async repository for local user management and authentication."""

    @staticmethod
    async def register(
        session: AsyncSession,
        username: str,
        password: str,
        full_name: Optional[str] = None,
        role: str = "engineer",
    ) -> User:
        """
        Register a new user with secure password hashing.
        Raises ValueError if username is already taken.
        """
        clean_username = username.strip().lower()
        if not clean_username:
            raise ValueError("Username cannot be empty")

        stmt = select(User).where(User.username == clean_username)
        res = await session.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing is not None:
            raise ValueError(f"Username '{clean_username}' already exists.")

        user = User(
            username=clean_username,
            password_hash=hash_password(password),
            full_name=full_name,
            role=role,
        )
        session.add(user)
        await session.flush()
        return user

    @staticmethod
    async def authenticate(
        session: AsyncSession,
        username: str,
        password: str,
    ) -> Optional[User]:
        """
        Authenticate user credentials.
        Returns User if password matches; otherwise None.
        """
        clean_username = username.strip().lower()
        stmt = select(User).where(User.username == clean_username)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()
        if user is None:
            return None

        if verify_password(password, user.password_hash):
            return user
        return None

    @staticmethod
    async def get_by_username(
        session: AsyncSession,
        username: str,
    ) -> Optional[User]:
        """Fetch user by username."""
        clean_username = username.strip().lower()
        stmt = select(User).where(User.username == clean_username)
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def list_users(
        session: AsyncSession,
        limit: int = 50,
    ) -> List[User]:
        """List registered local users (for air-gapped system admin)."""
        stmt = select(User).order_by(User.created_at.desc()).limit(limit)
        res = await session.execute(stmt)
        return list(res.scalars().all())
