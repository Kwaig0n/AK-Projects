"""Agent CRUD + trigger routes."""
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.agent import AgentConfig
from app.models.schemas import AgentCreate, AgentUpdate, AgentResponse, RunTriggerResponse, SkillResponse
from app.services.agent_service import trigger_run, get_agents_with_stats
from app.scheduler import scheduler

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=list[AgentResponse])
async def list_agents(db: AsyncSession = Depends(get_db)):
    rows = await get_agents_with_stats(db)
    return [AgentResponse(**row) for row in rows]


@router.get("/skills", response_model=list[SkillResponse])
async def list_skills():
    from app.agents.skills_registry import SKILLS
    return SKILLS


@router.post("", response_model=AgentResponse, status_code=201)
async def create_agent(data: AgentCreate, db: AsyncSession = Depends(get_db)):
    agent = AgentConfig(
        name=data.name,
        description=data.description,
        agent_type=data.agent_type,
        cron_expression=data.cron_expression,
        notify_telegram=data.notify_telegram,
        telegram_chat_id=data.telegram_chat_id,
        criteria=json.dumps(data.criteria),
        enabled_skills=json.dumps(data.enabled_skills),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    # Register scheduler job if cron provided
    if agent.cron_expression and agent.is_active:
        scheduler.register_job(agent.id, agent.name, agent.cron_expression)

    cols = {c.key: getattr(agent, c.key) for c in agent.__table__.columns}
    cols["criteria"] = json.loads(agent.criteria)
    cols["enabled_skills"] = json.loads(agent.enabled_skills) if agent.enabled_skills else []
    return AgentResponse(**cols)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: int, db: AsyncSession = Depends(get_db)):
    rows = await get_agents_with_stats(db)
    for row in rows:
        if row["id"] == agent_id:
            return AgentResponse(**row)
    raise HTTPException(status_code=404, detail="Agent not found")


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: int, data: AgentUpdate, db: AsyncSession = Depends(get_db)):
    agent = await db.get(AgentConfig, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if data.name is not None:
        agent.name = data.name
    if data.description is not None:
        agent.description = data.description
    if data.is_active is not None:
        agent.is_active = data.is_active
    if data.cron_expression is not None:
        agent.cron_expression = data.cron_expression or None
    if data.notify_telegram is not None:
        agent.notify_telegram = data.notify_telegram
    if data.telegram_chat_id is not None:
        agent.telegram_chat_id = data.telegram_chat_id or None
    if data.criteria is not None:
        agent.criteria = json.dumps(data.criteria)
    if data.enabled_skills is not None:
        agent.enabled_skills = json.dumps(data.enabled_skills)
    agent.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(agent)

    # Update scheduler
    if agent.cron_expression and agent.is_active:
        scheduler.register_job(agent.id, agent.name, agent.cron_expression)
    else:
        scheduler.remove_job(agent.id)

    rows = await get_agents_with_stats(db)
    for row in rows:
        if row["id"] == agent_id:
            return AgentResponse(**row)


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(agent_id: int, db: AsyncSession = Depends(get_db)):
    agent = await db.get(AgentConfig, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    scheduler.remove_job(agent_id)
    await db.delete(agent)
    await db.commit()


@router.post("/{agent_id}/run", response_model=RunTriggerResponse)
async def run_agent(agent_id: int, db: AsyncSession = Depends(get_db)):
    agent = await db.get(AgentConfig, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    run_id = await trigger_run(agent_id, triggered_by="dashboard")
    return RunTriggerResponse(run_id=run_id, message=f"Agent '{agent.name}' started")


@router.post("/{agent_id}/toggle", response_model=AgentResponse)
async def toggle_agent(agent_id: int, db: AsyncSession = Depends(get_db)):
    agent = await db.get(AgentConfig, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.is_active = not agent.is_active
    agent.updated_at = datetime.utcnow()
    await db.commit()

    if agent.is_active and agent.cron_expression:
        scheduler.register_job(agent.id, agent.name, agent.cron_expression)
    else:
        scheduler.remove_job(agent.id)

    rows = await get_agents_with_stats(db)
    for row in rows:
        if row["id"] == agent_id:
            return AgentResponse(**row)
