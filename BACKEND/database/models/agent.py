"""
Agentic Execution & Traceability Models for AGNI Air-Gapped Workbench.
Implements the Master Agentic Blueprint:
- Agent Tasks & Step-by-Step execution trace
- Autonomous industrial assumptions for vague queries (task_assumptions)
- Tool invocation telemetry (duration, inputs, outputs)
- Model registry and transparent routing decisions
- Generic deliverables (Word, Excel, PPT, Code)
- Lightweight zero-egress network event logging
"""

from typing import Optional, Any
from datetime import datetime
from sqlalchemy import String, Text, Integer, Float, Boolean, BigInteger, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, generate_uuid, utc_now


class ModelRegistry(Base):
    """Catalog of available open-weight models and specialized industrial roles."""
    __tablename__ = "model_registry"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    model_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # reasoning, coding, vision
    is_installed: Mapped[bool] = mapped_column(Boolean, default=False)
    context_window: Mapped[int] = mapped_column(Integer, default=8192)
    status: Mapped[str] = mapped_column(String(32), default="available", index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class KnowledgeSource(Base):
    """Hierarchical plant knowledge categories (SOPs, Standards, Manuals)."""
    __tablename__ = "knowledge_sources"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    source_name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # SOP, Standard, Manual
    connection_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    sync_status: Mapped[str] = mapped_column(String(32), default="synced")
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class AgentTask(Base):
    """Parent record for an agentic multi-step workflow or user goal."""
    __tablename__ = "agent_tasks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    conversation_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("users.username", ondelete="SET NULL"), nullable=True, index=True)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="in_progress", index=True)  # in_progress, completed, failed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    steps: Mapped[list["AgentTaskStep"]] = relationship("AgentTaskStep", back_populates="task", cascade="all, delete-orphan")
    assumptions: Mapped[list["TaskAssumption"]] = relationship("TaskAssumption", back_populates="task", cascade="all, delete-orphan")


class RoutingDecision(Base):
    """Audit trail of automatic model selection decisions."""
    __tablename__ = "routing_decisions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    task_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("agent_tasks.id", ondelete="CASCADE"), nullable=True, index=True)
    message_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    requested_task_type: Mapped[str] = mapped_column(String(64), nullable=False)  # reasoning, coding, vision
    candidate_models: Mapped[Optional[Any]] = mapped_column(JSON, default=list)
    selected_model: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class AgentTaskStep(Base):
    """Step-by-step trace of actions executed by the agent."""
    __tablename__ = "agent_task_steps"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    task_id: Mapped[str] = mapped_column(String(64), ForeignKey("agent_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    step_type: Mapped[str] = mapped_column(String(64), nullable=False)  # understand_query, rag_retrieval, determine_assumptions, code_calculation, generate_report
    tool_used: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    input_ref: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_ref: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="done")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    task: Mapped["AgentTask"] = relationship("AgentTask", back_populates="steps")
    tool_invocations: Mapped[list["ToolInvocation"]] = relationship("ToolInvocation", back_populates="step", cascade="all, delete-orphan")


class ToolInvocation(Base):
    """Granular execution record for each local tool invocation."""
    __tablename__ = "tool_invocations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    task_step_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("agent_task_steps.id", ondelete="CASCADE"), nullable=True, index=True)
    tool_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    input_payload: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    output_payload: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="success")
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0)
    invoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    step: Mapped[Optional["AgentTaskStep"]] = relationship("AgentTaskStep", back_populates="tool_invocations")


class TaskAssumption(Base):
    """Grounded industrial baseline assumptions determined for vague queries."""
    __tablename__ = "task_assumptions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    task_id: Mapped[str] = mapped_column(String(64), ForeignKey("agent_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    parameter_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    assumed_value: Mapped[str] = mapped_column(String(128), nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    source_document_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    source_chunk_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    standard_name: Mapped[str] = mapped_column(String(128), nullable=False)  # e.g., ASME B31.3, OISD 141
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=True)
    is_user_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    task: Mapped["AgentTask"] = relationship("AgentTask", back_populates="assumptions")


class Deliverable(Base):
    """Deliverable artifacts (Word, Excel, PPT, Python code)."""
    __tablename__ = "deliverables"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    task_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("agent_tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    step_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("agent_task_steps.id", ondelete="SET NULL"), nullable=True)
    deliverable_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # approval_note, calculation_report, board_presentation
    file_format: Mapped[str] = mapped_column(String(32), nullable=False)  # docx, xlsx, pptx, pdf, py
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    status: Mapped[str] = mapped_column(String(32), default="generated")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class NetworkEvent(Base):
    """Audit log of local-only network activity proving zero external egress."""
    __tablename__ = "network_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(128), default="127.0.0.1")
    destination: Mapped[str] = mapped_column(String(128), default="127.0.0.1")
    direction: Mapped[str] = mapped_column(String(32), default="LOCAL")
    connection_type: Mapped[str] = mapped_column(String(32), default="TCP")
    external_connection: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    bytes_transferred: Mapped[int] = mapped_column(BigInteger, default=0)
    blocked: Mapped[bool] = mapped_column(Boolean, default=False)
