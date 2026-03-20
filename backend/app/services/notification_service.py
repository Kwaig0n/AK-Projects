"""Formats and sends Telegram notifications for agent findings."""
from __future__ import annotations
import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.agent import AgentRun, Finding, AgentConfig

logger = logging.getLogger(__name__)

# Will be set when bot is initialized
_bot_instance = None


def set_bot(bot) -> None:
    global _bot_instance
    _bot_instance = bot


async def notify_run_complete(
    agent: "AgentConfig",
    run: "AgentRun",
    findings: list["Finding"],
) -> None:
    if not _bot_instance:
        return
    if not agent.notify_telegram:
        return

    chat_id = agent.telegram_chat_id or agent.notify_telegram
    from app.config import settings
    chat_id = agent.telegram_chat_id or settings.telegram_default_chat_id
    if not chat_id:
        logger.warning("No Telegram chat_id configured, skipping notification")
        return

    message = _format_run_complete(agent, run, findings)
    try:
        await _bot_instance.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {e}")


def _format_run_complete(agent: "AgentConfig", run: "AgentRun", findings: list["Finding"]) -> str:
    icon = "🏠" if agent.agent_type == "real_estate" else "🔍"
    duration = f"{run.duration_seconds:.0f}s" if run.duration_seconds else "?"
    count = len(findings)

    if count == 0:
        return (
            f"{icon} <b>{agent.name}</b> — Run Complete\n"
            f"⏱ {duration} | No new findings"
        )

    lines = [
        f"{icon} <b>{agent.name}</b> — Run Complete",
        f"⏱ {duration} | {count} new finding{'s' if count != 1 else ''}",
        "",
    ]

    for i, finding in enumerate(findings[:10], 1):
        meta = {}
        try:
            meta = json.loads(finding.metadata_json) if isinstance(finding.metadata_json, str) else finding.metadata_json
        except Exception:
            pass

        lines.append(f"<b>{i}. {finding.title}</b>")

        if agent.agent_type == "real_estate":
            parts = []
            if meta.get("price"):
                parts.append(f"💰 {meta['price']}")
            if meta.get("bedrooms"):
                parts.append(f"🛏 {meta['bedrooms']}")
            if meta.get("bathrooms"):
                parts.append(f"🚿 {meta['bathrooms']}")
            if parts:
                lines.append("   " + " | ".join(parts))

        lines.append(f"   Score: {finding.relevance_score:.2f} ★")
        if finding.url:
            lines.append(f"   {finding.url}")
        lines.append("")

    if count > 10:
        lines.append(f"... and {count - 10} more findings")

    return "\n".join(lines)
