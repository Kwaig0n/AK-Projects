"""Telegram bot command handlers and lifecycle."""
from __future__ import annotations
import asyncio
import json
import logging
from datetime import datetime, timedelta

from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes

from app.config import settings

logger = logging.getLogger(__name__)

_application: Application | None = None


async def start_bot() -> None:
    global _application
    if not settings.telegram_bot_token:
        logger.warning("No TELEGRAM_BOT_TOKEN set — bot disabled")
        return

    _application = Application.builder().token(settings.telegram_bot_token).build()

    # Register commands
    _application.add_handler(CommandHandler("start", cmd_start))
    _application.add_handler(CommandHandler("help", cmd_help))
    _application.add_handler(CommandHandler("status", cmd_status))
    _application.add_handler(CommandHandler("run", cmd_run))
    _application.add_handler(CommandHandler("results", cmd_results))
    _application.add_handler(CommandHandler("history", cmd_history))
    _application.add_handler(CommandHandler("criteria", cmd_criteria))
    _application.add_handler(CommandHandler("pause", cmd_pause))
    _application.add_handler(CommandHandler("resume", cmd_resume))

    await _application.bot.set_my_commands([
        BotCommand("status", "Show all agents status"),
        BotCommand("run", "Trigger an agent: /run <name>"),
        BotCommand("results", "Latest findings: /results [agent name]"),
        BotCommand("history", "Last 10 runs"),
        BotCommand("criteria", "Show agent criteria: /criteria <name>"),
        BotCommand("pause", "Pause scheduled runs: /pause <name>"),
        BotCommand("resume", "Resume scheduled runs: /resume <name>"),
        BotCommand("help", "Command reference"),
    ])

    await _application.initialize()
    await _application.start()
    await _application.updater.start_polling(drop_pending_updates=True)

    # Register bot instance for notifications
    from app.services import notification_service
    notification_service.set_bot(_application.bot)

    logger.info("Telegram bot started")


async def stop_bot() -> None:
    global _application
    if _application:
        await _application.updater.stop()
        await _application.stop()
        await _application.shutdown()
        logger.info("Telegram bot stopped")


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _get_agents():
    from app.database import AsyncSessionLocal
    from app.models.agent import AgentConfig
    from sqlalchemy import select
    async with AsyncSessionLocal() as db:
        return (await db.execute(select(AgentConfig).where(AgentConfig.is_active == True))).scalars().all()


async def _find_agent_by_name(name: str):
    agents = await _get_agents()
    name_lower = name.lower()
    for agent in agents:
        if name_lower in agent.name.lower():
            return agent
    return None


def _fmt_dt(dt: datetime | None) -> str:
    if not dt:
        return "Never"
    return dt.strftime("%d %b %H:%M")


# ── Command Handlers ──────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 <b>Agent Dashboard Bot</b>\n\n"
        "I'll notify you when your agents find new results, and you can control agents from here.\n\n"
        "Type /help to see all commands.",
        parse_mode="HTML",
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "<b>Available Commands</b>\n\n"
        "/status — All agents with status and last run\n"
        "/run &lt;name&gt; — Trigger an agent immediately\n"
        "/results — Latest findings (last 24h)\n"
        "/results &lt;name&gt; — Findings for specific agent\n"
        "/history — Last 10 runs across all agents\n"
        "/criteria &lt;name&gt; — Show agent search criteria\n"
        "/pause &lt;name&gt; — Pause scheduled runs\n"
        "/resume &lt;name&gt; — Resume scheduled runs\n"
        "/help — This message",
        parse_mode="HTML",
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from app.database import AsyncSessionLocal
    from app.services.agent_service import get_agents_with_stats
    async with AsyncSessionLocal() as db:
        agents = await get_agents_with_stats(db)

    if not agents:
        await update.message.reply_text("No agents configured yet.")
        return

    lines = ["<b>Agent Status</b>\n"]
    for a in agents:
        status_icon = "✅" if a["is_active"] else "⏸"
        agent_type_icon = "🏠" if a["agent_type"] == "real_estate" else "🔍"
        last_run = _fmt_dt(a.get("last_run_at"))
        last_status = a.get("last_run_status", "—")
        schedule = a.get("cron_expression") or "Manual only"
        lines.append(
            f"{status_icon} {agent_type_icon} <b>{a['name']}</b>\n"
            f"   Last run: {last_run} ({last_status})\n"
            f"   Schedule: {schedule}\n"
            f"   Findings (24h): {a['findings_last_24h']}\n"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def cmd_run(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /run <agent name>")
        return

    name = " ".join(context.args)
    agent = await _find_agent_by_name(name)
    if not agent:
        await update.message.reply_text(f"Agent '{name}' not found. Use /status to see agents.")
        return

    from app.services.agent_service import trigger_run
    await update.message.reply_text(f"🚀 Starting <b>{agent.name}</b>...", parse_mode="HTML")
    run_id = await trigger_run(agent.id, triggered_by="telegram")
    await update.message.reply_text(
        f"✅ Agent started (run ID: <code>{run_id[:8]}...</code>)\n"
        "You'll receive a notification when findings are ready.",
        parse_mode="HTML",
    )


async def cmd_results(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from app.database import AsyncSessionLocal
    from app.models.agent import Finding, AgentConfig
    from sqlalchemy import select, desc

    agent_filter = " ".join(context.args) if context.args else None
    cutoff = datetime.utcnow() - timedelta(hours=24)

    async with AsyncSessionLocal() as db:
        q = (
            select(Finding, AgentConfig.name)
            .join(AgentConfig, Finding.agent_id == AgentConfig.id)
            .where(Finding.discovered_at >= cutoff)
            .order_by(desc(Finding.relevance_score))
            .limit(10)
        )
        if agent_filter:
            q = q.where(AgentConfig.name.ilike(f"%{agent_filter}%"))
        rows = (await db.execute(q)).all()

    if not rows:
        msg = "No findings in the last 24 hours"
        if agent_filter:
            msg += f" for '{agent_filter}'"
        await update.message.reply_text(msg + ".")
        return

    lines = [f"<b>Latest Findings</b> (last 24h)\n"]
    for finding, agent_name in rows:
        icon = "🏠" if finding.finding_type == "listing" else "🔍"
        lines.append(
            f"{icon} <b>{finding.title}</b>\n"
            f"   Agent: {agent_name} | Score: {finding.relevance_score:.2f}\n"
            f"   {finding.summary[:100]}...\n"
        )
        if finding.url:
            lines.append(f"   {finding.url}\n")
        lines.append("")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from app.database import AsyncSessionLocal
    from app.models.agent import AgentRun, AgentConfig
    from sqlalchemy import select, desc

    async with AsyncSessionLocal() as db:
        rows = (await db.execute(
            select(AgentRun, AgentConfig.name)
            .join(AgentConfig, AgentRun.agent_id == AgentConfig.id)
            .order_by(desc(AgentRun.started_at))
            .limit(10)
        )).all()

    if not rows:
        await update.message.reply_text("No runs yet.")
        return

    lines = ["<b>Recent Runs</b>\n"]
    for run, agent_name in rows:
        icon = {"completed": "✅", "failed": "❌", "running": "⏳", "pending": "⏸"}.get(run.status, "❓")
        duration = f"{run.duration_seconds:.0f}s" if run.duration_seconds else "?"
        lines.append(
            f"{icon} <b>{agent_name}</b>\n"
            f"   {_fmt_dt(run.started_at)} · {duration} · {run.findings_count} findings\n"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def cmd_criteria(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /criteria <agent name>")
        return

    name = " ".join(context.args)
    agent = await _find_agent_by_name(name)
    if not agent:
        await update.message.reply_text(f"Agent '{name}' not found.")
        return

    criteria = json.loads(agent.criteria) if isinstance(agent.criteria, str) else agent.criteria
    formatted = json.dumps(criteria, indent=2)
    await update.message.reply_text(
        f"<b>{agent.name}</b> — Criteria\n\n<pre>{formatted}</pre>",
        parse_mode="HTML",
    )


async def cmd_pause(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /pause <agent name>")
        return
    name = " ".join(context.args)
    agent = await _find_agent_by_name(name)
    if not agent:
        await update.message.reply_text(f"Agent '{name}' not found.")
        return
    from app.scheduler import scheduler
    scheduler.pause_job(agent.id)
    await update.message.reply_text(f"⏸ Paused scheduled runs for <b>{agent.name}</b>.", parse_mode="HTML")


async def cmd_resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /resume <agent name>")
        return
    name = " ".join(context.args)
    agent = await _find_agent_by_name(name)
    if not agent:
        await update.message.reply_text(f"Agent '{name}' not found.")
        return
    from app.scheduler import scheduler
    scheduler.resume_job(agent.id)
    await update.message.reply_text(f"▶️ Resumed scheduled runs for <b>{agent.name}</b>.", parse_mode="HTML")
