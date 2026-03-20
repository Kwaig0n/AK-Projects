"""Base agentic loop using Claude tool use."""
from __future__ import annotations
import asyncio
import json
import logging
from datetime import datetime
from typing import Callable, Any

import anthropic

from app.config import settings
from app.agents.tools.registry import TOOL_REGISTRY
from app.agents.tools.web_search import SEARCH_WEB_TOOL_DEF
from app.agents.tools.web_scraper import SCRAPE_PAGE_TOOL_DEF
from app.agents.tools.real_estate import SEARCH_REAL_ESTATE_TOOL_DEF

logger = logging.getLogger(__name__)

REPORT_FINDING_TOOL_DEF = {
    "name": "report_finding",
    "description": (
        "Report a discovered finding to be saved and notified. "
        "Call this for EACH significant result you find. "
        "Only report findings that genuinely match the user's criteria."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Clear title for the finding, e.g. '3BR House - Newtown NSW $750,000'",
            },
            "url": {
                "type": "string",
                "description": "URL of the listing or source page",
            },
            "summary": {
                "type": "string",
                "description": "1-3 sentence summary of why this finding is relevant",
            },
            "finding_type": {
                "type": "string",
                "enum": ["listing", "price_change", "research_result", "alert"],
            },
            "relevance_score": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "How well does this match the criteria? 1.0 = perfect, 0.7 = close",
            },
            "metadata": {
                "type": "object",
                "description": "Structured data: price, bedrooms, bathrooms, location, etc.",
            },
        },
        "required": ["title", "summary", "finding_type", "relevance_score"],
    },
}

ALL_TOOLS = [
    SEARCH_WEB_TOOL_DEF,
    SCRAPE_PAGE_TOOL_DEF,
    SEARCH_REAL_ESTATE_TOOL_DEF,
    REPORT_FINDING_TOOL_DEF,
]


class FindingData:
    def __init__(self, title: str, summary: str, finding_type: str, relevance_score: float,
                 url: str | None = None, metadata: dict | None = None):
        self.title = title
        self.summary = summary
        self.finding_type = finding_type
        self.relevance_score = relevance_score
        self.url = url
        self.metadata = metadata or {}


class BaseAgent:
    """Base class for all agents. Subclasses override system_prompt and available_tools."""

    AGENT_TYPE = "base"

    def __init__(
        self,
        agent_id: int,
        run_id: str,
        criteria: dict[str, Any],
        log_fn: Callable[[str, str], None],
    ):
        self.agent_id = agent_id
        self.run_id = run_id
        self.criteria = criteria
        self.log = log_fn  # (level, message)
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.messages: list[dict] = []
        self.findings: list[FindingData] = []
        self.tokens_used = 0

    def get_system_prompt(self) -> str:
        raise NotImplementedError

    def get_initial_message(self) -> str:
        raise NotImplementedError

    def get_tools(self) -> list[dict]:
        """Return tool definitions for this agent. Subclasses can restrict."""
        return ALL_TOOLS

    async def execute(self) -> list[FindingData]:
        """Run the agentic loop until completion or iteration limit."""
        self.log("info", f"Agent starting (type={self.AGENT_TYPE})")
        self.messages = [{"role": "user", "content": self.get_initial_message()}]

        for iteration in range(settings.max_agent_iterations):
            self.log("info", f"Iteration {iteration + 1}/{settings.max_agent_iterations}")

            try:
                response = await asyncio.to_thread(
                    self.client.messages.create,
                    model="claude-sonnet-4-6",
                    max_tokens=8096,
                    system=self.get_system_prompt(),
                    tools=self.get_tools(),
                    messages=self.messages,
                )
            except anthropic.APIError as e:
                self.log("error", f"Claude API error: {e}")
                raise

            self.tokens_used += response.usage.input_tokens + response.usage.output_tokens
            self.messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                self.log("info", "Agent completed reasoning")
                break

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = await self._dispatch_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        })
                self.messages.append({"role": "user", "content": tool_results})
            else:
                self.log("warning", f"Unexpected stop reason: {response.stop_reason}")
                break

        self.log("info", f"Run complete. Found {len(self.findings)} findings. Tokens used: {self.tokens_used}")
        return self.findings

    async def _dispatch_tool(self, name: str, inputs: dict) -> Any:
        """Dispatch a tool call, handling report_finding specially."""
        if name == "report_finding":
            return self._handle_report_finding(inputs)

        self.log("tool_call", f"Tool: {name}({json.dumps(inputs)[:200]})")

        fn = TOOL_REGISTRY.get(name)
        if not fn:
            self.log("warning", f"Unknown tool: {name}")
            return {"error": f"Tool '{name}' not found"}

        result = await fn(**inputs)
        # Truncate large results for log readability
        result_str = json.dumps(result)
        preview = result_str[:300] + "..." if len(result_str) > 300 else result_str
        self.log("tool_result", f"Result: {preview}")
        return result

    def _handle_report_finding(self, inputs: dict) -> dict:
        """Handle the report_finding tool call — store locally."""
        finding = FindingData(
            title=inputs.get("title", "Untitled"),
            summary=inputs.get("summary", ""),
            finding_type=inputs.get("finding_type", "research_result"),
            relevance_score=float(inputs.get("relevance_score", 0.0)),
            url=inputs.get("url"),
            metadata=inputs.get("metadata", {}),
        )
        self.findings.append(finding)
        self.log(
            "info",
            f"Finding reported: {finding.title} (score={finding.relevance_score:.2f})"
        )
        return {"status": "saved", "finding_number": len(self.findings)}
