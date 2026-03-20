from datetime import datetime
from sqlalchemy import Integer, String, Boolean, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class AgentConfig(Base):
    __tablename__ = "agent_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False)  # real_estate | research
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    cron_expression: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notify_telegram: Mapped[bool] = mapped_column(Boolean, default=True)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    criteria: Mapped[str] = mapped_column(Text, default="{}")  # JSON blob
    enabled_skills: Mapped[str] = mapped_column(Text, default="[]")  # JSON list of skill IDs
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    runs: Mapped[list["AgentRun"]] = relationship("AgentRun", back_populates="agent", cascade="all, delete-orphan")
    findings: Mapped[list["Finding"]] = relationship("Finding", back_populates="agent", cascade="all, delete-orphan")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[int] = mapped_column(Integer, ForeignKey("agent_configs.id"), nullable=False)
    run_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)  # UUID
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|running|completed|failed
    triggered_by: Mapped[str] = mapped_column(String(20), default="dashboard")  # scheduler|dashboard|telegram|api
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    findings_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    log_entries: Mapped[str] = mapped_column(Text, default="[]")  # JSON array

    agent: Mapped["AgentConfig"] = relationship("AgentConfig", back_populates="runs")
    findings: Mapped[list["Finding"]] = relationship("Finding", back_populates="run", cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(Integer, ForeignKey("agent_runs.id"), nullable=False)
    agent_id: Mapped[int] = mapped_column(Integer, ForeignKey("agent_configs.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    raw_data: Mapped[str] = mapped_column(Text, default="{}")  # JSON
    finding_type: Mapped[str] = mapped_column(String(50), default="research_result")  # listing|price_change|research_result|alert
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_new: Mapped[bool] = mapped_column(Boolean, default=True)
    notified: Mapped[bool] = mapped_column(Boolean, default=False)
    discovered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")  # JSON: price, bedrooms, etc.

    run: Mapped["AgentRun"] = relationship("AgentRun", back_populates="findings")
    agent: Mapped["AgentConfig"] = relationship("AgentConfig", back_populates="findings")
