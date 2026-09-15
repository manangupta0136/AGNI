"""
Agentic Workflow, Planning, Assumptions & Tool Traceability Repository.
Provides async persistence and query methods for the master AGNI agentic architecture.
"""

from typing import List, Optional, Any, Dict
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.agent import (
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
from database.base import utc_now


class AgentRepository:
    """Async repository for agentic tasks, multi-step traces, assumptions, and deliverables."""

    # ── Agent Tasks ──────────────────────────────────────────────────────────
    @staticmethod
    async def create_task(
        session: AsyncSession,
        goal: str,
        conversation_id: Optional[str] = None,
        username: Optional[str] = None,
    ) -> AgentTask:
        """Create a new parent agent task."""
        task = AgentTask(
            goal=goal,
            conversation_id=conversation_id,
            username=username,
            status="in_progress",
        )
        session.add(task)
        await session.flush()
        return task

    @staticmethod
    async def get_task(
        session: AsyncSession,
        task_id: str,
    ) -> Optional[AgentTask]:
        """Fetch an agent task by ID."""
        stmt = select(AgentTask).where(AgentTask.id == task_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def complete_task(
        session: AsyncSession,
        task_id: str,
        status: str = "completed",
    ) -> Optional[AgentTask]:
        """Mark an agent task as completed or failed."""
        task = await AgentRepository.get_task(session, task_id)
        if task:
            task.status = status
            task.completed_at = utc_now()
            await session.flush()
        return task

    # ── Agent Task Steps ─────────────────────────────────────────────────────
    @staticmethod
    async def add_task_step(
        session: AsyncSession,
        task_id: str,
        step_index: int,
        step_type: str,
        tool_used: Optional[str] = None,
        input_ref: Optional[str] = None,
        output_ref: Optional[str] = None,
        status: str = "done",
    ) -> AgentTaskStep:
        """Record an individual execution step within an agent task."""
        step = AgentTaskStep(
            task_id=task_id,
            step_index=step_index,
            step_type=step_type,
            tool_used=tool_used,
            input_ref=input_ref,
            output_ref=output_ref,
            status=status,
            finished_at=utc_now() if status == "done" else None,
        )
        session.add(step)
        await session.flush()
        return step

    @staticmethod
    async def list_task_steps(
        session: AsyncSession,
        task_id: str,
    ) -> List[AgentTaskStep]:
        """List all steps for a specific task in execution order."""
        stmt = (
            select(AgentTaskStep)
            .where(AgentTaskStep.task_id == task_id)
            .order_by(AgentTaskStep.step_index.asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    # ── Tool Invocations ─────────────────────────────────────────────────────
    @staticmethod
    async def log_tool_invocation(
        session: AsyncSession,
        tool_name: str,
        task_step_id: Optional[str] = None,
        input_payload: Optional[Any] = None,
        output_payload: Optional[Any] = None,
        duration_ms: float = 0.0,
        status: str = "success",
    ) -> ToolInvocation:
        """Record granular tool call metrics and payloads."""
        inv = ToolInvocation(
            task_step_id=task_step_id,
            tool_name=tool_name,
            input_payload=input_payload,
            output_payload=output_payload,
            duration_ms=duration_ms,
            status=status,
        )
        session.add(inv)
        await session.flush()
        return inv

    # ── Task Assumptions (Crucial for Vague Query Disambiguation) ─────────────
    @staticmethod
    async def record_task_assumption(
        session: AsyncSession,
        task_id: str,
        parameter_name: str,
        assumed_value: str,
        standard_name: str,
        reason: str,
        unit: Optional[str] = None,
        source_document_id: Optional[str] = None,
        source_chunk_id: Optional[str] = None,
        is_default: bool = True,
    ) -> TaskAssumption:
        """Record an autonomous grounded baseline assumption for a vague query."""
        assumption = TaskAssumption(
            task_id=task_id,
            parameter_name=parameter_name,
            assumed_value=assumed_value,
            unit=unit,
            source_document_id=source_document_id,
            source_chunk_id=source_chunk_id,
            standard_name=standard_name,
            reason=reason,
            is_default=is_default,
        )
        session.add(assumption)
        await session.flush()
        return assumption

    @staticmethod
    async def list_task_assumptions(
        session: AsyncSession,
        task_id: str,
    ) -> List[TaskAssumption]:
        """Fetch all assumed baseline parameters for a task."""
        stmt = (
            select(TaskAssumption)
            .where(TaskAssumption.task_id == task_id)
            .order_by(TaskAssumption.created_at.asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    # ── Routing Decisions (Model Auto-Selection Audit) ────────────────────────
    @staticmethod
    async def record_routing_decision(
        session: AsyncSession,
        requested_task_type: str,
        selected_model: str,
        reason: str,
        task_id: Optional[str] = None,
        message_id: Optional[str] = None,
        candidate_models: Optional[List[str]] = None,
    ) -> RoutingDecision:
        """Record model auto-selection provenance for hackathon auditability."""
        decision = RoutingDecision(
            task_id=task_id,
            message_id=message_id,
            requested_task_type=requested_task_type,
            candidate_models=candidate_models or [],
            selected_model=selected_model,
            reason=reason,
        )
        session.add(decision)
        await session.flush()
        return decision

    @staticmethod
    async def list_routing_decisions(
        session: AsyncSession,
        limit: int = 20,
    ) -> List[RoutingDecision]:
        """Fetch recent model selection decisions."""
        stmt = (
            select(RoutingDecision)
            .order_by(RoutingDecision.decided_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    # ── Model Registry ───────────────────────────────────────────────────────
    @staticmethod
    async def register_model(
        session: AsyncSession,
        model_id: str,
        display_name: str,
        task_type: str,
        is_installed: bool = True,
        context_window: int = 8192,
        notes: Optional[str] = None,
    ) -> ModelRegistry:
        """Register or update an open-weight model in the registry."""
        stmt = select(ModelRegistry).where(ModelRegistry.model_id == model_id)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.display_name = display_name
            existing.task_type = task_type
            existing.is_installed = is_installed
            existing.notes = notes
            await session.flush()
            return existing

        model = ModelRegistry(
            model_id=model_id,
            display_name=display_name,
            task_type=task_type,
            is_installed=is_installed,
            context_window=context_window,
            notes=notes,
        )
        session.add(model)
        await session.flush()
        return model

    @staticmethod
    async def list_registered_models(
        session: AsyncSession,
    ) -> List[ModelRegistry]:
        """List all models registered in the workbench catalog."""
        stmt = select(ModelRegistry).order_by(ModelRegistry.created_at.asc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    # ── Deliverables (Word, Excel, PPT, Code) ────────────────────────────────
    @staticmethod
    async def create_deliverable(
        session: AsyncSession,
        title: str,
        deliverable_type: str,
        file_format: str,
        file_path: str,
        task_id: Optional[str] = None,
        step_id: Optional[str] = None,
        file_size_bytes: int = 0,
    ) -> Deliverable:
        """Register a newly generated deliverable file."""
        deliverable = Deliverable(
            title=title,
            deliverable_type=deliverable_type,
            file_format=file_format,
            file_path=file_path,
            task_id=task_id,
            step_id=step_id,
            file_size_bytes=file_size_bytes,
        )
        session.add(deliverable)
        await session.flush()
        return deliverable

    @staticmethod
    async def list_deliverables(
        session: AsyncSession,
        task_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Deliverable]:
        """Fetch deliverables created by the agent."""
        stmt = select(Deliverable)
        if task_id:
            stmt = stmt.where(Deliverable.task_id == task_id)
        stmt = stmt.order_by(Deliverable.created_at.desc()).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    # ── Network Events (Air-Gap Sovereign Audit) ──────────────────────────────
    @staticmethod
    async def log_network_event(
        session: AsyncSession,
        source: str = "127.0.0.1",
        destination: str = "127.0.0.1",
        direction: str = "LOCAL",
        connection_type: str = "TCP",
        external_connection: bool = False,
        bytes_transferred: int = 0,
        blocked: bool = False,
    ) -> NetworkEvent:
        """Record network event for sovereign air-gap telemetry."""
        event = NetworkEvent(
            source=source,
            destination=destination,
            direction=direction,
            connection_type=connection_type,
            external_connection=external_connection,
            bytes_transferred=bytes_transferred,
            blocked=blocked,
        )
        session.add(event)
        await session.flush()
        return event

    @staticmethod
    async def get_network_summary(
        session: AsyncSession,
    ) -> Dict[str, Any]:
        """Return zero-egress compliance metrics."""
        ext_stmt = select(func.count(NetworkEvent.id)).where(NetworkEvent.external_connection == True)
        ext_count = (await session.execute(ext_stmt)).scalar() or 0

        tot_stmt = select(func.count(NetworkEvent.id))
        total_count = (await session.execute(tot_stmt)).scalar() or 0

        return {
            "external_connections_detected": ext_count,
            "total_local_events": total_count,
            "air_gap_compliant": (ext_count == 0),
            "status": "SECURE_LOCAL_ONLY" if ext_count == 0 else "EGRESS_ALERT",
        }
