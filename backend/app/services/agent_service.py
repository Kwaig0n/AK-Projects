"""Orchestration layer: trigger runs, save findings, bridge to scheduler and Telegram."""
from __future__ import annotations
import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.agent import AgentConfig, AgentRun, Finding
from app.services import sse_service, notification_service

if TYPE_CHECKING:
    from app.agents.base_agent import FindingData

logger = logging.getLogger(__name__)

# Live asyncio Tasks keyed by run_id — cancelled directly on stop request
_RUNNING_TASKS: dict[str, "asyncio.Task[None]"] = {}

# Kept for between-iteration checks in base_agent
_STOP_REQUESTS: set[str] = set()


def request_stop(run_id: str) -> None:
    """Immediately cancel the running agent task."""
    _STOP_REQUESTS.add(run_id)
    task = _RUNNING_TASKS.get(run_id)
    if task and not task.done():
        task.cancel()


def is_stop_requested(run_id: str) -> bool:
    return run_id in _STOP_REQUESTS


def clear_stop(run_id: str) -> None:
    _STOP_REQUESTS.discard(run_id)


def _make_log_fn(run_id: str, log_store: list[dict]):
    """Create a log function that writes to SSE bus and local list."""
    def log_fn(level: str, message: str):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
        }
        log_store.append(entry)
        sse_service.emit_log(run_id, level, message)
    return log_fn


async def trigger_run(agent_id: int, triggered_by: str = "dashboard") -> str:
    """Start an agent run asynchronously. Returns run_id."""
    run_id = str(uuid.uuid4())
    task = asyncio.create_task(_run_agent(agent_id, run_id, triggered_by))
    _RUNNING_TASKS[run_id] = task
    return run_id


async def _run_agent(agent_id: int, run_id: str, triggered_by: str) -> None:
    """Full agent execution lifecycle."""
    log_store: list[dict] = []
    log = _make_log_fn(run_id, log_store)
    start_time = datetime.utcnow()
    agent_instance = None

    async with AsyncSessionLocal() as db:
        agent = await db.get(AgentConfig, agent_id)
        if not agent:
            logger.error(f"Agent {agent_id} not found")
            _RUNNING_TASKS.pop(run_id, None)
            return

        # Create run record
        run = AgentRun(
            agent_id=agent_id,
            run_id=run_id,
            status="running",
            triggered_by=triggered_by,
            started_at=start_time,
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)
        run_db_id = run.id

        findings_data: list[FindingData] = []

        try:
            criteria = json.loads(agent.criteria) if isinstance(agent.criteria, str) else agent.criteria
            enabled_skills = json.loads(agent.enabled_skills) if isinstance(agent.enabled_skills, str) else (agent.enabled_skills or [])
            agent_instance = _create_agent(agent.agent_type, agent_id, run_id, criteria, log, enabled_skills)
            findings_data = await agent_instance.execute()

        except asyncio.CancelledError:
            # Task was cancelled via request_stop() — mark as stopped and persist findings so far
            clear_stop(run_id)
            log("warning", "Run stopped by user")
            sse_service.emit_log(run_id, "done", "Run stopped by user")

            duration = (datetime.utcnow() - start_time).total_seconds()
            run.status = "stopped"
            run.completed_at = datetime.utcnow()
            run.duration_seconds = duration
            run.findings_count = len(agent_instance.findings) if agent_instance else 0
            run.tokens_used = agent_instance.tokens_used if agent_instance else 0
            run.log_entries = json.dumps(log_store)
            await db.commit()
            sse_service.cleanup_run(run_id)
            _RUNNING_TASKS.pop(run_id, None)
            return

        except Exception as e:
            logger.exception(f"Agent run {run_id} failed: {e}")
            log("error", f"Agent failed: {e}")
            sse_service.emit_log(run_id, "done", "Run failed")

            run.status = "failed"
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
            run.duration_seconds = (datetime.utcnow() - start_time).total_seconds()
            run.log_entries = json.dumps(log_store)
            await db.commit()
            _RUNNING_TASKS.pop(run_id, None)
            return

        # Save findings
        saved_findings = []
        for fd in findings_data:
            is_new = True
            if fd.url:
                existing = await db.scalar(
                    select(Finding).where(
                        Finding.agent_id == agent_id,
                        Finding.url == fd.url,
                    )
                )
                if existing:
                    is_new = False

            finding = Finding(
                run_id=run_db_id,
                agent_id=agent_id,
                title=fd.title,
                url=fd.url,
                summary=fd.summary,
                finding_type=fd.finding_type,
                relevance_score=fd.relevance_score,
                is_new=is_new,
                notified=False,
                metadata_json=json.dumps(fd.metadata),
            )
            db.add(finding)
            saved_findings.append(finding)

        duration = (datetime.utcnow() - start_time).total_seconds()
        sse_service.emit_log(run_id, "done", f"Completed in {duration:.1f}s")

        run.status = "completed"
        run.completed_at = datetime.utcnow()
        run.duration_seconds = duration
        run.findings_count = len(saved_findings)
        run.tokens_used = agent_instance.tokens_used
        run.log_entries = json.dumps(log_store)
        await db.commit()

        for f in saved_findings:
            await db.refresh(f)

        new_findings = [f for f in saved_findings if f.is_new]
        if new_findings and agent.notify_telegram:
            await notification_service.notify_run_complete(agent, run, new_findings)

        for f in new_findings:
            f.notified = True
        await db.commit()

        sse_service.cleanup_run(run_id)
        _RUNNING_TASKS.pop(run_id, None)


def _create_agent(agent_type: str, agent_id: int, run_id: str, criteria: dict, log_fn, enabled_skills: list[str] | None = None):
    """Instantiate the correct agent class."""
    from app.agents.real_estate_agent import RealEstateAgent
    from app.agents.research_agent import ResearchAgent

    if agent_type == "real_estate":
        return RealEstateAgent(agent_id, run_id, criteria, log_fn, enabled_skills)
    elif agent_type == "research":
        return ResearchAgent(agent_id, run_id, criteria, log_fn, enabled_skills)
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")


# ── Query helpers ────────────────────────────────────────────────────────────

async def get_agents_with_stats(db: AsyncSession) -> list[dict]:
    agents = (await db.execute(select(AgentConfig).order_by(AgentConfig.created_at))).scalars().all()
    result = []
    cutoff = datetime.utcnow() - timedelta(hours=24)

    for agent in agents:
        # Last run
        last_run = (await db.execute(
            select(AgentRun)
            .where(AgentRun.agent_id == agent.id)
            .order_by(desc(AgentRun.started_at))
            .limit(1)
        )).scalar_one_or_none()

        # Findings last 24h
        findings_24h = await db.scalar(
            select(func.count(Finding.id)).where(
                Finding.agent_id == agent.id,
                Finding.discovered_at >= cutoff,
            )
        )

        # Next run (from scheduler)
        next_run_at = None
        if agent.cron_expression and agent.is_active:
            try:
                from croniter import croniter
                cron = croniter(agent.cron_expression, datetime.utcnow())
                next_run_at = cron.get_next(datetime)
            except Exception:
                pass

        row = {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "agent_type": agent.agent_type,
            "is_active": agent.is_active,
            "cron_expression": agent.cron_expression,
            "notify_telegram": agent.notify_telegram,
            "telegram_chat_id": agent.telegram_chat_id,
            "criteria": json.loads(agent.criteria) if isinstance(agent.criteria, str) else agent.criteria,
            "enabled_skills": json.loads(agent.enabled_skills) if isinstance(agent.enabled_skills, str) else (agent.enabled_skills or []),
            "created_at": agent.created_at,
            "updated_at": agent.updated_at,
            "last_run_status": last_run.status if last_run else None,
            "last_run_at": last_run.started_at if last_run else None,
            "last_run_id": last_run.run_id if last_run else None,
            "next_run_at": next_run_at,
            "findings_last_24h": findings_24h or 0,
        }
        result.append(row)

    return result
