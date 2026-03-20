"""News search skill using Tavily with recency focus."""
import logging
from app.config import settings

logger = logging.getLogger(__name__)

NEWS_MONITOR_TOOL_DEF = {
    "name": "search_news",
    "description": (
        "Search for recent news articles about a specific topic. "
        "Better than search_web for finding current events and recent publications."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "News search query, e.g. 'Sydney property market interest rates 2024'",
            },
            "num_results": {
                "type": "integer",
                "description": "Number of news results to return (1-10)",
                "default": 5,
            },
        },
        "required": ["query"],
    },
}


async def search_news(query: str, num_results: int = 5) -> dict:
    """Search for recent news using Tavily news topic."""
    if not settings.tavily_api_key:
        return {"error": "Tavily API key not configured", "results": []}

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=settings.tavily_api_key)
        response = client.search(
            query=query,
            max_results=min(num_results, 10),
            search_depth="basic",
            topic="news",
        )
        results = [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("content", ""),
                "published_date": r.get("published_date", ""),
            }
            for r in response.get("results", [])
        ]
        return {"results": results, "query": query}
    except Exception as e:
        logger.warning(f"News search with topic=news failed ({e}), falling back to web search")
        # Fallback: regular search with "news recent" appended
        from app.agents.tools.web_search import search_web
        return await search_web(f"{query} news recent", num_results)
