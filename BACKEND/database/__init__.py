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
    User,
    hash_password,
    verify_password,
    Conversation,
    Message,
    Document,
    DocumentChunk,
    LongTermMemory,
    AuditReport,
    SecurityAuditLog,
    CodeExecutionRun,
    VisionAnalysis,
    AgentTask,
    AgentTaskStep,
    ToolInvocation,
    TaskAssumption,
    Deliverable,
    ModelRegistry,
    RoutingDecision,
    KnowledgeSource,
    NetworkEvent,
)
from database.repositories import (
    UserRepository,
    MemoryRepository,
    ChatRepository,
    DocumentRepository,
    AuditRepository,
    AgentRepository,
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
    "User",
    "hash_password",
    "verify_password",
    "Conversation",
    "Message",
    "Document",
    "DocumentChunk",
    "LongTermMemory",
    "AuditReport",
    "SecurityAuditLog",
    "CodeExecutionRun",
    "VisionAnalysis",
    "AgentTask",
    "AgentTaskStep",
    "ToolInvocation",
    "TaskAssumption",
    "Deliverable",
    "ModelRegistry",
    "RoutingDecision",
    "KnowledgeSource",
    "NetworkEvent",
    # Repositories
    "UserRepository",
    "MemoryRepository",
    "ChatRepository",
    "DocumentRepository",
    "AuditRepository",
    "AgentRepository",
]

