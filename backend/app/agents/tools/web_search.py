"""Tavily web search tool."""
import logging
from app.config import settings

logger = logging.getLogger(__name__)


async def search_web(query: str, num_results: int = 5) -> dict:
    """Search the web using Tavily API."""
    if not settings.tavily_api_key:
        return {"error": "Tavily API key not configured", "results": []}

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=settings.tavily_api_key)
        response = client.search(
            query=query,
            max_results=min(num_results, 10),
            search_depth="basic",
        )
        results = [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("content", ""),
            }
            for r in response.get("results", [])
        ]
        return {"results": results, "query": query}
    except Exception as e:
        logger.error(f"Tavily search error: {e}")
        return {"error": str(e), "results": []}


SEARCH_WEB_TOOL_DEF = {
    "name": "search_web",
    "description": (
        "Search the web for information using a query string. "
        "Returns titles, URLs, and content snippets from relevant pages."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query string",
            },
            "num_results": {
                "type": "integer",
                "description": "Number of results to return (1-10)",
                "default": 5,
            },
        },
        "required": ["query"],
    },
}
