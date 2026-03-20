"""Maps tool names (as Claude knows them) to async callable implementations."""
from app.agents.tools.web_search import search_web
from app.agents.tools.web_scraper import scrape_page
from app.agents.tools.real_estate import search_real_estate

TOOL_REGISTRY: dict[str, callable] = {
    "search_web": search_web,
    "scrape_page": scrape_page,
    "search_real_estate": search_real_estate,
    # report_finding is handled specially by the agent, not dispatched here
}
