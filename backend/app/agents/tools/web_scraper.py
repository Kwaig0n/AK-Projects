"""Generic web page scraper using httpx + BeautifulSoup."""
import asyncio
import logging
import httpx
from bs4 import BeautifulSoup
from app.config import settings

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-AU,en;q=0.9",
}


async def scrape_page(url: str, extract_fields: list[str] | None = None) -> dict:
    """Fetch a URL and extract its text content."""
    await asyncio.sleep(settings.agent_request_delay_seconds)
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=20, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        # Remove scripts, styles, nav, footer
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        # Collapse whitespace
        lines = [line for line in text.splitlines() if line.strip()]
        cleaned = "\n".join(lines[:200])  # Cap at 200 lines

        result = {"url": url, "content": cleaned, "status": response.status_code}

        if extract_fields:
            extracted = {}
            for field in extract_fields:
                extracted[field] = _extract_field(soup, field)
            result["extracted"] = extracted

        return result

    except httpx.HTTPStatusError as e:
        return {"url": url, "error": f"HTTP {e.response.status_code}", "content": ""}
    except Exception as e:
        logger.error(f"Scrape error for {url}: {e}")
        return {"url": url, "error": str(e), "content": ""}


def _extract_field(soup: BeautifulSoup, field: str) -> str:
    """Heuristic field extractor."""
    field_lower = field.lower()
    selectors = {
        "price": ["[data-testid*='price']", ".price", "#price", "[class*='price']"],
        "address": ["[data-testid*='address']", ".address", "[class*='address']"],
        "bedrooms": ["[data-testid*='bed']", "[class*='bedroom']", "[class*='bed-']"],
        "bathrooms": ["[data-testid*='bath']", "[class*='bathroom']"],
        "description": ["[data-testid*='description']", ".description", "#description"],
    }
    for selector in selectors.get(field_lower, []):
        el = soup.select_one(selector)
        if el:
            return el.get_text(strip=True)
    return ""


SCRAPE_PAGE_TOOL_DEF = {
    "name": "scrape_page",
    "description": (
        "Fetch and extract text content from a URL. "
        "Optionally extracts specific fields like price, address, bedrooms. "
        "Use this to get full details from a listing or article page."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to fetch",
            },
            "extract_fields": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional specific fields to extract, e.g. ['price', 'address', 'bedrooms', 'bathrooms']",
            },
        },
        "required": ["url"],
    },
}
