"""Job listing search tool using Tavily site: queries."""
import logging
from app.config import settings

logger = logging.getLogger(__name__)

_SOURCE_PREFIXES = {
    "seek.com.au": "site:seek.com.au",
    "linkedin.com": "site:linkedin.com/jobs",
    "indeed.com.au": "site:au.indeed.com",
    "indeed.com": "site:indeed.com",
    "glassdoor.com": "site:glassdoor.com/job",
}


async def search_jobs(
    query: str,
    location: str | None = None,
    source: str = "seek.com.au",
    num_results: int = 5,
) -> dict:
    """Search a job board using Tavily and return listing titles, URLs, and snippets."""
    if not settings.tavily_api_key:
        return {"error": "Tavily API key not configured", "results": []}

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=settings.tavily_api_key)

        prefix = _SOURCE_PREFIXES.get(source, f"site:{source}")
        full_query = f"{prefix} {query}"
        if location:
            full_query += f" {location}"

        response = client.search(
            query=full_query,
            max_results=min(num_results, 10),
            search_depth="basic",
        )

        results = [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("content", ""),
                "source": source,
            }
            for r in response.get("results", [])
        ]
        return {"results": results, "query": full_query, "source": source}

    except Exception as e:
        logger.error(f"Job search error ({source}): {e}")
        return {"error": str(e), "results": []}


SEARCH_JOBS_TOOL_DEF = {
    "name": "search_jobs",
    "description": (
        "Search job listings on Seek, LinkedIn, Indeed, or Glassdoor. "
        "Returns job titles, URLs, and description snippets. "
        "Use scrape_page on the returned URLs to get the full job description."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Job title or keywords, e.g. 'Python developer', 'product manager'",
            },
            "location": {
                "type": "string",
                "description": "Location to filter by, e.g. 'Sydney', 'Melbourne', 'Remote'",
            },
            "source": {
                "type": "string",
                "enum": ["seek.com.au", "linkedin.com", "indeed.com.au", "glassdoor.com"],
                "description": "Job board to search (default: seek.com.au)",
                "default": "seek.com.au",
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
