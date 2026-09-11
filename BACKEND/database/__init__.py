"""
AGNI Database Package.
Provides async PostgreSQL connectivity, SQLAlchemy 2.0 ORM models, and repositories.
"""

from database.base import Base, generate_uuid, utc_now
from database.connection import (
    init_db,
    close_db,
    get_db,
    get_engine,
    get_session_factory,
    check_db_connection,
)
from database.models import (
    Conversation,
    Message,
    Document,
    DocumentChunk,
    AuditReport,
    SecurityAuditLog,
    CodeExecutionRun,
    VisionAnalysis,
)
from database.repositories import (
    ChatRepository,
    DocumentRepository,
    AuditRepository,
)

__all__ = [
    # Base & Connection
    "Base",
    "generate_uuid",
    "utc_now",
    "init_db",
    "close_db",
    "get_db",
    "get_engine",
    "get_session_factory",
    "check_db_connection",
    # Models
    "Conversation",
    "Message",
    "Document",
    "DocumentChunk",
    "AuditReport",
    "SecurityAuditLog",
    "CodeExecutionRun",
    "VisionAnalysis",
    # Repositories
    "ChatRepository",
    "DocumentRepository",
    "AuditRepository",
]
