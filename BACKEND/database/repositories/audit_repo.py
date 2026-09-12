"""
Audit, Compliance, Sandbox & Vision Repository for AGNI Air-Gapped Workbench.
Handles forensic security logging, code execution runs, report tracking, and vision analysis.
"""

from typing import List, Optional, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.audit import SecurityAuditLog, CodeExecutionRun
from database.models.report import AuditReport
from database.models.vision import VisionAnalysis


class AuditRepository:
    """Async repository for security audits, sandbox logs, reports, and vision analyses."""

    # ── Security Audit Logs ──────────────────────────────────────────────────
    @staticmethod
    async def log_security_event(
        session: AsyncSession,
        event_type: str,
        severity: str = "INFO",
        ip_address: str = "127.0.0.1",
        request_id: Optional[str] = None,
        external_connections_detected: int = 0,
        details: Optional[Any] = None,
    ) -> SecurityAuditLog:
        """Create a verifiable security audit log entry."""
        entry = SecurityAuditLog(
            event_type=event_type,
            severity=severity,
            ip_address=ip_address,
            request_id=request_id,
            external_connections_detected=external_connections_detected,
            details=details or {},
        )
        session.add(entry)
        await session.flush()
        return entry

    @staticmethod
    async def list_security_logs(
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
        severity: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> List[SecurityAuditLog]:
        """Fetch recent forensic security events."""
        stmt = select(SecurityAuditLog)
        if severity:
            stmt = stmt.where(SecurityAuditLog.severity == severity)
        if event_type:
            stmt = stmt.where(SecurityAuditLog.event_type == event_type)
        stmt = stmt.order_by(SecurityAuditLog.timestamp.desc()).limit(limit).offset(offset)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    # ── Code Sandbox Execution Runs ──────────────────────────────────────────
    @staticmethod
    async def log_code_execution(
        session: AsyncSession,
        code_snippet: str,
        status: str,
        stdout: str = "",
        stderr: str = "",
        execution_time_ms: float = 0.0,
        conversation_id: Optional[str] = None,
        language: str = "python",
    ) -> CodeExecutionRun:
        """Record an isolated code sandbox execution."""
        run = CodeExecutionRun(
            code_snippet=code_snippet,
            status=status,
            stdout=stdout,
            stderr=stderr,
            execution_time_ms=execution_time_ms,
            conversation_id=conversation_id,
            language=language,
        )
        session.add(run)
        await session.flush()
        return run

    @staticmethod
    async def list_code_executions(
        session: AsyncSession,
        conversation_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[CodeExecutionRun]:
        """Retrieve past code execution runs."""
        stmt = select(CodeExecutionRun)
        if conversation_id:
            stmt = stmt.where(CodeExecutionRun.conversation_id == conversation_id)
        stmt = stmt.order_by(CodeExecutionRun.executed_at.desc()).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    # ── Generated Audit Reports ──────────────────────────────────────────────
    @staticmethod
    async def create_audit_report(
        session: AsyncSession,
        title: str,
        file_path: str,
        file_size_bytes: int = 0,
        conversation_id: Optional[str] = None,
        document_ids: Optional[Any] = None,
        report_type: str = "Industrial Inspection Audit",
    ) -> AuditReport:
        """Register a newly generated .docx / .pdf compliance report."""
        rep = AuditReport(
            title=title,
            file_path=file_path,
            file_size_bytes=file_size_bytes,
            conversation_id=conversation_id,
            document_ids=document_ids or [],
            report_type=report_type,
        )
        session.add(rep)
        await session.flush()
        return rep

    @staticmethod
    async def list_audit_reports(
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AuditReport]:
        """List generated inspection reports."""
        stmt = (
            select(AuditReport)
            .order_by(AuditReport.generated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    # ── Vision Analyses ──────────────────────────────────────────────────────
    @staticmethod
    async def create_vision_analysis(
        session: AsyncSession,
        session_id: str,
        image_path: str,
        image_hash: Optional[str] = None,
        prompt: Optional[str] = None,
        scan_summary: Optional[str] = None,
        detected_defects: Optional[Any] = None,
        model_used: str = "qwen2-vl:7b",
    ) -> VisionAnalysis:
        """Record findings of an equipment or blueprint vision scan."""
        vis = VisionAnalysis(
            session_id=session_id,
            image_path=image_path,
            image_hash=image_hash,
            prompt=prompt,
            scan_summary=scan_summary,
            detected_defects=detected_defects or [],
            model_used=model_used,
        )
        session.add(vis)
        await session.flush()
        return vis

    @staticmethod
    async def list_vision_analyses(
        session: AsyncSession,
        session_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[VisionAnalysis]:
        """List vision inspection records."""
        stmt = select(VisionAnalysis)
        if session_id:
            stmt = stmt.where(VisionAnalysis.session_id == session_id)
        stmt = stmt.order_by(VisionAnalysis.created_at.desc()).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())
