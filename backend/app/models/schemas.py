from datetime import datetime
from typing import Any
from pydantic import BaseModel, field_validator
import json


# ── Agent Schemas ────────────────────────────────────────────────────────────

class AgentCreate(BaseModel):
    name: str
    description: str = ""
    agent_type: str  # real_estate | research
    cron_expression: str | None = None
    notify_telegram: bool = True
    telegram_chat_id: str | None = None
    criteria: dict[str, Any] = {}
    enabled_skills: list[str] = []


class AgentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None
    cron_expression: str | None = None
    notify_telegram: bool | None = None
    telegram_chat_id: str | None = None
    criteria: dict[str, Any] | None = None
    enabled_skills: list[str] | None = None


class AgentResponse(BaseModel):
    id: int
    name: str
    description: str
    agent_type: str
    is_active: bool
    cron_expression: str | None
    notify_telegram: bool
    telegram_chat_id: str | None
    criteria: dict[str, Any]
    enabled_skills: list[str] = []
    created_at: datetime
    updated_at: datetime
    last_run_status: str | None = None
    last_run_at: datetime | None = None
    last_run_id: str | None = None
    next_run_at: datetime | None = None
    findings_last_24h: int = 0

    @field_validator("criteria", mode="before")
    @classmethod
    def parse_criteria(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("enabled_skills", mode="before")
    @classmethod
    def parse_skills(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return []
        return v or []

    model_config = {"from_attributes": True}


# ── Skill Schema ──────────────────────────────────────────────────────────────

class SkillResponse(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    compatible_types: list[str]


# ── Run Schemas ──────────────────────────────────────────────────────────────

class RunResponse(BaseModel):
    id: int
    agent_id: int
    run_id: str
    status: str
    triggered_by: str
    started_at: datetime | None
    completed_at: datetime | None
    duration_seconds: float | None
    findings_count: int
    error_message: str | None
    tokens_used: int
    log_entries: list[dict[str, Any]]
    agent_name: str | None = None

    @field_validator("log_entries", mode="before")
    @classmethod
    def parse_logs(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    model_config = {"from_attributes": True}


class RunTriggerResponse(BaseModel):
    run_id: str
    message: str


# ── Finding Schemas ──────────────────────────────────────────────────────────

class FindingResponse(BaseModel):
    id: int
    run_id: int
    agent_id: int
    title: str
    url: str | None
    summary: str
    finding_type: str
    relevance_score: float
    is_new: bool
    notified: bool
    discovered_at: datetime
    metadata_json: dict[str, Any]
    agent_name: str | None = None

    @field_validator("metadata_json", mode="before")
    @classmethod
    def parse_metadata(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    model_config = {"from_attributes": True}


class UnreadCountResponse(BaseModel):
    count: int


# ── SSE Log Entry ────────────────────────────────────────────────────────────

class LogEntry(BaseModel):
    timestamp: str
    level: str  # info | tool_call | tool_result | warning | error | done
    message: str
