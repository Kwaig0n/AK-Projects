"""Findings list, mark-read, and unread count routes."""
import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.agent import Finding, AgentConfig
from app.models.schemas import FindingResponse, UnreadCountResponse

router = APIRouter(prefix="/findings", tags=["findings"])


def _finding_to_response(finding: Finding, agent_name: str | None = None) -> FindingResponse:
    return FindingResponse(
        id=finding.id,
        run_id=finding.run_id,
        agent_id=finding.agent_id,
        title=finding.title,
        url=finding.url,
        summary=finding.summary,
        finding_type=finding.finding_type,
        relevance_score=finding.relevance_score,
        is_new=finding.is_new,
        notified=finding.notified,
        discovered_at=finding.discovered_at,
        metadata_json=json.loads(finding.metadata_json) if isinstance(finding.metadata_json, str) else finding.metadata_json,
        agent_name=agent_name,
    )


@router.get("", response_model=list[FindingResponse])
async def list_findings(
    agent_id: int | None = None,
    finding_type: str | None = None,
    is_new: bool | None = None,
    min_score: float | None = None,
    since_hours: int | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(Finding, AgentConfig.name)
        .join(AgentConfig, Finding.agent_id == AgentConfig.id)
        .order_by(desc(Finding.discovered_at))
    )
    if agent_id:
        q = q.where(Finding.agent_id == agent_id)
    if finding_type:
        q = q.where(Finding.finding_type == finding_type)
    if is_new is not None:
        q = q.where(Finding.is_new == is_new)
    if min_score is not None:
        q = q.where(Finding.relevance_score >= min_score)
    if since_hours:
        cutoff = datetime.utcnow() - timedelta(hours=since_hours)
        q = q.where(Finding.discovered_at >= cutoff)

    q = q.offset(offset).limit(limit)
    rows = (await db.execute(q)).all()
    return [_finding_to_response(f, name) for f, name in rows]


@router.get("/unread-count", response_model=UnreadCountResponse)
async def unread_count(db: AsyncSession = Depends(get_db)):
    count = await db.scalar(select(func.count(Finding.id)).where(Finding.is_new == True))
    return UnreadCountResponse(count=count or 0)


@router.get("/{finding_id}", response_model=FindingResponse)
async def get_finding(finding_id: int, db: AsyncSession = Depends(get_db)):
    row = (await db.execute(
        select(Finding, AgentConfig.name)
        .join(AgentConfig, Finding.agent_id == AgentConfig.id)
        .where(Finding.id == finding_id)
    )).first()
    if not row:
        raise HTTPException(status_code=404, detail="Finding not found")
    return _finding_to_response(row[0], row[1])


@router.put("/{finding_id}/read", response_model=FindingResponse)
async def mark_read(finding_id: int, db: AsyncSession = Depends(get_db)):
    finding = await db.get(Finding, finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    finding.is_new = False
    await db.commit()
    await db.refresh(finding)
    return _finding_to_response(finding)


@router.post("/mark-all-read", response_model=UnreadCountResponse)
async def mark_all_read(agent_id: int | None = None, db: AsyncSession = Depends(get_db)):
    q = select(Finding).where(Finding.is_new == True)
    if agent_id:
        q = q.where(Finding.agent_id == agent_id)
    findings = (await db.execute(q)).scalars().all()
    for f in findings:
        f.is_new = False
    await db.commit()
    return UnreadCountResponse(count=0)
