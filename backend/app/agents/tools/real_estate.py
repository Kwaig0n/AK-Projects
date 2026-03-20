"""Real estate listing search tools for Domain.com.au and realestate.com.au."""
import asyncio
import logging
import re
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
    "Accept-Language": "en-AU,en;q=0.9",
}


async def search_real_estate(
    location: str,
    source: str,
    price_min: int | None = None,
    price_max: int | None = None,
    bedrooms_min: int | None = None,
    property_type: str = "any",
) -> dict:
    """Search real estate listing sites with structured filters."""
    await asyncio.sleep(settings.agent_request_delay_seconds)

    source = source.lower()
    try:
        if "domain" in source:
            return await _search_domain(location, price_min, price_max, bedrooms_min, property_type)
        elif "realestate" in source or "rea" in source:
            return await _search_rea(location, price_min, price_max, bedrooms_min, property_type)
        elif "zillow" in source:
            return await _search_via_tavily(location, source, price_min, price_max, bedrooms_min, property_type)
        elif "rightmove" in source:
            return await _search_via_tavily(location, source, price_min, price_max, bedrooms_min, property_type)
        else:
            return await _search_via_tavily(location, source, price_min, price_max, bedrooms_min, property_type)
    except Exception as e:
        logger.error(f"Real estate search error ({source}): {e}")
        return {"error": str(e), "listings": []}


async def _search_domain(
    location: str,
    price_min: int | None,
    price_max: int | None,
    bedrooms_min: int | None,
    property_type: str,
) -> dict:
    """Scrape Domain.com.au search results."""
    # Normalize location for URL
    location_slug = location.lower().replace(" ", "-").replace(",", "")
    url = f"https://www.domain.com.au/sale/{location_slug}/"

    params = {}
    if price_min:
        params["price"] = f"{price_min}-{price_max or ''}"
    elif price_max:
        params["price"] = f"-{price_max}"
    if bedrooms_min:
        params["bedrooms"] = f"{bedrooms_min}-any"
    if property_type and property_type != "any":
        type_map = {"house": "house", "apartment": "apartment", "townhouse": "townhouse"}
        if property_type in type_map:
            params["property-types"] = type_map[property_type]

    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=20, follow_redirects=True) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return await _search_via_tavily(location, "domain.com.au", price_min, price_max, bedrooms_min, property_type)

        soup = BeautifulSoup(resp.text, "lxml")
        listings = []

        # Domain uses data-testid attributes on listing cards
        cards = soup.select("[data-testid='listing-card-wrapper-premiumplus'], [data-testid='listing-card-wrapper']")
        if not cards:
            # Fallback to class-based selection
            cards = soup.select(".css-qrqvvg, [class*='listing-card']")

        for card in cards[:20]:
            listing = _parse_domain_card(card)
            if listing:
                listings.append(listing)

        if not listings:
            # If scraping failed, fall back to Tavily
            return await _search_via_tavily(location, "domain.com.au", price_min, price_max, bedrooms_min, property_type)

        return {"source": "domain.com.au", "location": location, "listings": listings}

    except Exception as e:
        logger.error(f"Domain scrape error: {e}")
        return await _search_via_tavily(location, "domain.com.au", price_min, price_max, bedrooms_min, property_type)


def _parse_domain_card(card) -> dict | None:
    """Parse a Domain.com.au listing card."""
    try:
        title_el = card.select_one("[data-testid='listing-card-address'], h2, .address")
        price_el = card.select_one("[data-testid='listing-card-price'], .price, [class*='price']")
        link_el = card.select_one("a[href*='/property']")
        bed_el = card.select_one("[data-testid='property-features-bed'], [class*='bed']")
        bath_el = card.select_one("[data-testid='property-features-bath'], [class*='bath']")
        car_el = card.select_one("[data-testid='property-features-car'], [class*='car']")

        title = title_el.get_text(strip=True) if title_el else "Unknown address"
        price = price_el.get_text(strip=True) if price_el else "Price not listed"
        url = "https://www.domain.com.au" + link_el["href"] if link_el and link_el.get("href") else ""
        beds = _extract_number(bed_el.get_text(strip=True)) if bed_el else None
        baths = _extract_number(bath_el.get_text(strip=True)) if bath_el else None
        cars = _extract_number(car_el.get_text(strip=True)) if car_el else None

        return {
            "title": title,
            "price": price,
            "url": url,
            "bedrooms": beds,
            "bathrooms": baths,
            "parking": cars,
            "source": "domain.com.au",
        }
    except Exception:
        return None


async def _search_rea(
    location: str,
    price_min: int | None,
    price_max: int | None,
    bedrooms_min: int | None,
    property_type: str,
) -> dict:
    """Scrape realestate.com.au search results."""
    location_slug = location.lower().replace(" ", "-").replace(",", "")
    url = f"https://www.realestate.com.au/buy/in-{location_slug}/list-1"

    params = {}
    if price_min or price_max:
        price_str = f"price-{price_min or 0}-{price_max or 'any'}"
        url = url.replace("list-1", f"{price_str}/list-1")
    if bedrooms_min:
        params["numBeds"] = f"{bedrooms_min}-any"

    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=20, follow_redirects=True) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return await _search_via_tavily(location, "realestate.com.au", price_min, price_max, bedrooms_min, property_type)

        soup = BeautifulSoup(resp.text, "lxml")
        listings = []

        cards = soup.select("[data-testid='results-card'], .residential-card, [class*='listing-']")
        for card in cards[:20]:
            listing = _parse_rea_card(card)
            if listing:
                listings.append(listing)

        if not listings:
            return await _search_via_tavily(location, "realestate.com.au", price_min, price_max, bedrooms_min, property_type)

        return {"source": "realestate.com.au", "location": location, "listings": listings}

    except Exception as e:
        logger.error(f"REA scrape error: {e}")
        return await _search_via_tavily(location, "realestate.com.au", price_min, price_max, bedrooms_min, property_type)


def _parse_rea_card(card) -> dict | None:
    """Parse a realestate.com.au listing card."""
    try:
        title_el = card.select_one("[data-testid='address'], .property-info-address, h2")
        price_el = card.select_one("[data-testid='price'], .property-price, [class*='price']")
        link_el = card.select_one("a")
        bed_el = card.select_one("[data-testid='beds'], [class*='bed']")
        bath_el = card.select_one("[data-testid='baths'], [class*='bath']")

        title = title_el.get_text(strip=True) if title_el else "Unknown address"
        price = price_el.get_text(strip=True) if price_el else "Price not listed"
        href = link_el["href"] if link_el and link_el.get("href") else ""
        url = href if href.startswith("http") else f"https://www.realestate.com.au{href}"
        beds = _extract_number(bed_el.get_text(strip=True)) if bed_el else None
        baths = _extract_number(bath_el.get_text(strip=True)) if bath_el else None

        return {
            "title": title,
            "price": price,
            "url": url,
            "bedrooms": beds,
            "bathrooms": baths,
            "source": "realestate.com.au",
        }
    except Exception:
        return None


async def _search_via_tavily(
    location: str,
    source: str,
    price_min: int | None,
    price_max: int | None,
    bedrooms_min: int | None,
    property_type: str,
) -> dict:
    """Fall back to Tavily web search for real estate listings."""
    from app.agents.tools.web_search import search_web

    parts = [f"site:{source}" if source not in ("any", "") else ""]
    parts.append(f"real estate for sale {location}")
    if property_type and property_type != "any":
        parts.append(property_type)
    if bedrooms_min:
        parts.append(f"{bedrooms_min} bedroom")
    if price_min or price_max:
        price_part = f"${price_min:,}" if price_min else ""
        if price_max:
            price_part += f"-${price_max:,}"
        parts.append(price_part)

    query = " ".join(p for p in parts if p)
    results = await search_web(query, num_results=10)

    listings = []
    for r in results.get("results", []):
        listings.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "snippet": r.get("snippet", ""),
            "source": source,
        })

    return {"source": source, "location": location, "listings": listings, "via_search": True}


def _extract_number(text: str) -> int | None:
    """Extract first integer from text."""
    match = re.search(r"\d+", text)
    return int(match.group()) if match else None


SEARCH_REAL_ESTATE_TOOL_DEF = {
    "name": "search_real_estate",
    "description": (
        "Search real estate listing sites with structured filters. "
        "Returns matching property listings with price, bedrooms, and URL. "
        "Supports domain.com.au, realestate.com.au, zillow, rightmove."
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
