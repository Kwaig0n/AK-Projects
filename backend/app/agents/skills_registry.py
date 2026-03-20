"""Registry of optional skills (extra tools) that can be enabled per agent."""
from app.agents.tools.news_monitor import NEWS_MONITOR_TOOL_DEF
from app.agents.tools.calculator import CALCULATOR_TOOL_DEF

# Displayed in the dashboard — shown to user as toggleable options
SKILLS: list[dict] = [
    {
        "id": "news_monitor",
        "name": "News Monitor",
        "description": "Search recent news articles on any topic. Great for tracking market news, suburb developments, or research topics.",
        "icon": "newspaper",
        "compatible_types": ["real_estate", "research"],
    },
    {
        "id": "calculator",
        "name": "Financial Calculator",
        "description": "Perform mortgage repayments, ROI, stamp duty, and other financial calculations mid-run.",
        "icon": "calculator",
        "compatible_types": ["real_estate", "research"],
    },
]

# Maps skill ID -> Claude tool definition
SKILL_TOOL_DEFS: dict[str, dict] = {
    "news_monitor": NEWS_MONITOR_TOOL_DEF,
    "calculator": CALCULATOR_TOOL_DEF,
}
