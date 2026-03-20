"""Run history and SSE log streaming routes."""
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.agent import AgentRun, AgentConfig
from app.models.schemas import RunResponse
from app.services import sse_service

router = APIRouter(prefix="/runs", tags=["runs"])


def _run_to_response(run: AgentRun, agent_name: str | None = None) -> RunResponse:
    return RunResponse(
        id=run.id,
        agent_id=run.agent_id,
        run_id=run.run_id,
        status=run.status,
        triggered_by=run.triggered_by,
        started_at=run.started_at,
        completed_at=run.completed_at,
        duration_seconds=run.duration_seconds,
        findings_count=run.findings_count,
        error_message=run.error_message,
        tokens_used=run.tokens_used,
        log_entries=json.loads(run.log_entries) if isinstance(run.log_entries, str) else run.log_entries,
        agent_name=agent_name,
    )


@router.get("", response_model=list[RunResponse])
async def list_runs(
    agent_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = select(AgentRun, AgentConfig.name).join(AgentConfig, AgentRun.agent_id == AgentConfig.id)
    if agent_id:
        q = q.where(AgentRun.agent_id == agent_id)
    q = q.order_by(desc(AgentRun.started_at)).offset(offset).limit(limit)
    rows = (await db.execute(q)).all()
    return [_run_to_response(run, name) for run, name in rows]


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(run_id: str, db: AsyncSession = Depends(get_db)):
    row = (await db.execute(
        select(AgentRun, AgentConfig.name)
        .join(AgentConfig, AgentRun.agent_id == AgentConfig.id)
        .where(AgentRun.run_id == run_id)
    )).first()
    if not row:
        raise HTTPException(status_code=404, detail="Run not found")
    run, name = row
    return _run_to_response(run, name)


@router.get("/{run_id}/stream")
async def stream_run_logs(run_id: str):
    """SSE endpoint: streams live log entries while a run is active."""
    return StreamingResponse(
        sse_service.stream_logs(run_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{run_id}/stop", status_code=200)
async def stop_run(run_id: str, db: AsyncSession = Depends(get_db)):
    """Request a running agent to stop after its current iteration."""
    from app.services.agent_service import request_stop
    run = (await db.execute(select(AgentRun).where(AgentRun.run_id == run_id))).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status != "running":
        raise HTTPException(status_code=400, detail=f"Run is not running (status: {run.status})")
    request_stop(run_id)
    return {"message": "Stop requested"}


@router.delete("/{run_id}", status_code=204)
async def delete_run(run_id: str, db: AsyncSession = Depends(get_db)):
    run = (await db.execute(select(AgentRun).where(AgentRun.run_id == run_id))).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    await db.delete(run)
    await db.commit()
