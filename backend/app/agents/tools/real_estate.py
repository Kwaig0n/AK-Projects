"""Real estate listing search — Tavily-first approach (no direct scraping of listing sites)."""
import asyncio
import logging
import re
from app.config import settings

logger = logging.getLogger(__name__)


async def search_real_estate(
    location: str,
    source: str,
    price_min: int | None = None,
    price_max: int | None = None,
    bedrooms_min: int | None = None,
    property_type: str = "any",
) -> dict:
    """Search real estate listing sites via Tavily with domain filtering."""
    await asyncio.sleep(settings.agent_request_delay_seconds)

    source = source.lower()

    # Map source to domain filter for Tavily
    domain_map = {
        "domain.com.au": "domain.com.au",
        "realestate.com.au": "realestate.com.au",
        "zillow": "zillow.com",
        "rightmove": "rightmove.co.uk",
    }
    include_domain = next((v for k, v in domain_map.items() if k in source), None)

    try:
        return await _search_via_tavily(
            location=location,
            source=source,
            include_domain=include_domain,
            price_min=price_min,
            price_max=price_max,
            bedrooms_min=bedrooms_min,
            property_type=property_type,
        )
    except Exception as e:
        logger.error(f"Real estate search error ({source}): {e}")
        return {"error": str(e), "listings": []}


async def _search_via_tavily(
    location: str,
    source: str,
    include_domain: str | None,
    price_min: int | None,
    price_max: int | None,
    bedrooms_min: int | None,
    property_type: str,
) -> dict:
    """Search real estate listings using Tavily with domain filtering."""
    if not settings.tavily_api_key:
        return {"error": "Tavily API key not configured", "listings": []}

    # Build a targeted query
    parts = ["property for sale", location]
    if property_type and property_type != "any":
        parts.append(property_type)
    if bedrooms_min:
        parts.append(f"{bedrooms_min}+ bedrooms")
    if price_min and price_max:
        parts.append(f"${price_min:,} to ${price_max:,}")
    elif price_max:
        parts.append(f"under ${price_max:,}")
    elif price_min:
        parts.append(f"over ${price_min:,}")

    query = " ".join(parts)

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=settings.tavily_api_key)

        kwargs = {
            "query": query,
            "max_results": 10,
            "search_depth": "advanced",
        }
        if include_domain:
            kwargs["include_domains"] = [include_domain]

        response = client.search(**kwargs)
        raw_results = response.get("results", [])

        listings = []
        for r in raw_results:
            title = r.get("title", "")
            url = r.get("url", "")
            content = r.get("content", "")

            # Try to extract price from content
            price = _extract_price(content) or _extract_price(title) or "See listing"
            beds = _extract_beds(content) or _extract_beds(title)
            baths = _extract_baths(content) or _extract_baths(title)

            listings.append({
                "title": title,
                "url": url,
                "snippet": content[:400],
                "price": price,
                "bedrooms": beds,
                "bathrooms": baths,
                "source": include_domain or source,
            })

        return {
            "source": include_domain or source,
            "location": location,
            "query": query,
            "listings": listings,
            "via_tavily": True,
        }

    except Exception as e:
        logger.error(f"Tavily real estate search error: {e}")
        return {"error": str(e), "listings": []}


def _extract_price(text: str) -> str | None:
    """Extract price string from text."""
    match = re.search(r"\$[\d,]+(?:\s*(?:million|m|k))?", text, re.IGNORECASE)
    return match.group() if match else None


def _extract_beds(text: str) -> int | None:
    """Extract bedroom count from text."""
    match = re.search(r"(\d+)\s*(?:bed(?:room)?s?|bd)", text, re.IGNORECASE)
    return int(match.group(1)) if match else None


def _extract_baths(text: str) -> int | None:
    """Extract bathroom count from text."""
    match = re.search(r"(\d+)\s*(?:bath(?:room)?s?|ba)", text, re.IGNORECASE)
    return int(match.group(1)) if match else None


SEARCH_REAL_ESTATE_TOOL_DEF = {
    "name": "search_real_estate",
    "description": (
        "Search real estate listing sites for properties matching your criteria. "
        "Uses Tavily to search domain.com.au, realestate.com.au, zillow, or rightmove. "
        "Returns listings with price, bedrooms, URL, and snippets."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "Suburb, city, or area to search, e.g. 'Newtown NSW' or 'Inner West Sydney'",
            },
            "source": {
                "type": "string",
                "description": "Listing site to search",
                "enum": ["domain.com.au", "realestate.com.au", "zillow", "rightmove"],
            },
            "price_min": {
                "type": "integer",
                "description": "Minimum price in local currency (no commas)",
            },
            "price_max": {
                "type": "integer",
                "description": "Maximum price in local currency (no commas)",
            },
            "bedrooms_min": {
                "type": "integer",
                "description": "Minimum number of bedrooms",
            },
            "property_type": {
                "type": "string",
                "enum": ["house", "apartment", "townhouse", "any"],
                "description": "Type of property",
                "default": "any",
            },
        },
        "required": ["location", "source"],
    },
}
