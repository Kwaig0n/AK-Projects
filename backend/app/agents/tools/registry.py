"""Maps tool names (as Claude knows them) to async callable implementations."""
from app.agents.tools.web_search import search_web
from app.agents.tools.web_scraper import scrape_page
from app.agents.tools.real_estate import search_real_estate
from app.agents.tools.rental import get_rental_estimate
from app.agents.tools.news_monitor import search_news
from app.agents.tools.calculator import calculate
from app.agents.tools.job_search import search_jobs

TOOL_REGISTRY: dict[str, callable] = {
    "search_web": search_web,
    "scrape_page": scrape_page,
    "search_real_estate": search_real_estate,
    "get_rental_estimate": get_rental_estimate,
    "search_news": search_news,
    "calculate": calculate,
    "search_jobs": search_jobs,
    # report_finding is handled specially by the agent, not dispatched here
}
