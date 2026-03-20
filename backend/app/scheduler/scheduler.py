"""APScheduler setup for cron-based agent runs."""
import asyncio
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="Australia/Sydney")


def start(agent_service) -> None:
    """Start the scheduler and load existing agent jobs from DB."""
    scheduler.start()
    logger.info("Scheduler started")
    # Jobs are registered by the API when agents are created/updated.
    # On startup we reload from DB (called from lifespan).


async def load_jobs_from_db() -> None:
    """Register cron jobs for all active agents with schedules."""
    from app.database import AsyncSessionLocal
    from app.models.agent import AgentConfig
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        agents = (await db.execute(
            select(AgentConfig).where(
                AgentConfig.is_active == True,
                AgentConfig.cron_expression != None,
            )
        )).scalars().all()

    for agent in agents:
        register_job(agent.id, agent.name, agent.cron_expression)

    logger.info(f"Loaded {len(agents)} scheduled agent job(s)")


def register_job(agent_id: int, agent_name: str, cron_expression: str) -> None:
    """Add or update a scheduler job for an agent."""
    from app.services.agent_service import trigger_run

    job_id = f"agent_{agent_id}"
    try:
        scheduler.add_job(
            func=lambda: asyncio.create_task(trigger_run(agent_id, triggered_by="scheduler")),
            trigger=CronTrigger.from_crontab(cron_expression),
            id=job_id,
            name=agent_name,
            replace_existing=True,
            misfire_grace_time=300,
        )
        logger.info(f"Registered job {job_id} with cron '{cron_expression}'")
    except Exception as e:
        logger.error(f"Failed to register job for agent {agent_id}: {e}")


def remove_job(agent_id: int) -> None:
    """Remove a scheduled job."""
    job_id = f"agent_{agent_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info(f"Removed job {job_id}")


def pause_job(agent_id: int) -> None:
    job_id = f"agent_{agent_id}"
    if scheduler.get_job(job_id):
        scheduler.pause_job(job_id)


def resume_job(agent_id: int) -> None:
    job_id = f"agent_{agent_id}"
    if scheduler.get_job(job_id):
        scheduler.resume_job(job_id)


def get_job_info(agent_id: int) -> dict | None:
    job = scheduler.get_job(f"agent_{agent_id}")
    if not job:
        return None
    return {
        "id": job.id,
        "name": job.name,
        "next_run": job.next_run_time,
        "trigger": str(job.trigger),
    }


def list_all_jobs() -> list[dict]:
    return [
        {
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time,
            "trigger": str(job.trigger),
        }
        for job in scheduler.get_jobs()
    ]


def stop() -> None:
    scheduler.shutdown(wait=True)
    logger.info("Scheduler stopped")
