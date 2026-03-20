"""Rental yield estimation tool.

Searches rental listings for similar properties in the same suburb to estimate:
- Weekly rent (median of comparable rentals)
- Rental yield % = (weekly_rent * 52) / purchase_price * 100
- Suburb average yield (based on median rent / median sale price)
- Yield index = property_yield / suburb_avg_yield  (>1.0 = above suburb average)
"""
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


async def get_rental_estimate(
    location: str,
    bedrooms: int | None = None,
    property_type: str = "any",
    purchase_price: int | None = None,
) -> dict:
    """
    Estimate rental yield for a property by finding comparable rental listings nearby.
    Returns weekly rent estimate, rental yield %, suburb avg yield, and yield index.
    """
    await asyncio.sleep(settings.agent_request_delay_seconds)

    # Search for rentals via Tavily (most reliable cross-source approach)
    rental_data = await _search_rentals_tavily(location, bedrooms, property_type)
    sale_data = await _search_sales_tavily(location, bedrooms, property_type)

    weekly_rents = rental_data.get("weekly_rents", [])
    sale_prices = sale_data.get("sale_prices", [])

    if not weekly_rents:
        return {
            "error": "Could not find comparable rental listings",
            "location": location,
            "weekly_rents_found": 0,
        }

    # Median weekly rent for comparable properties
    weekly_rents.sort()
    n = len(weekly_rents)
    median_weekly_rent = weekly_rents[n // 2] if n % 2 else (weekly_rents[n // 2 - 1] + weekly_rents[n // 2]) / 2

    result = {
        "location": location,
        "bedrooms": bedrooms,
        "property_type": property_type,
        "median_weekly_rent": round(median_weekly_rent),
        "weekly_rent_range": {
            "min": min(weekly_rents),
            "max": max(weekly_rents),
        },
        "comparable_rentals_found": n,
    }

    # Rental yield for this specific property
    if purchase_price and purchase_price > 0:
        property_yield = (median_weekly_rent * 52) / purchase_price * 100
        result["purchase_price"] = purchase_price
        result["annual_rental_income"] = round(median_weekly_rent * 52)
        result["rental_yield_pct"] = round(property_yield, 2)

    # Suburb average yield (median rent / median sale price)
    if sale_prices:
        sale_prices.sort()
        ns = len(sale_prices)
        median_sale_price = sale_prices[ns // 2] if ns % 2 else (sale_prices[ns // 2 - 1] + sale_prices[ns // 2]) / 2
        suburb_avg_yield = (median_weekly_rent * 52) / median_sale_price * 100
        result["suburb_median_sale_price"] = round(median_sale_price)
        result["suburb_avg_yield_pct"] = round(suburb_avg_yield, 2)
        result["comparable_sales_found"] = len(sale_prices)

        # Yield index: how does this property compare to suburb average?
        if purchase_price and purchase_price > 0:
            property_yield = (median_weekly_rent * 52) / purchase_price * 100
            yield_index = property_yield / suburb_avg_yield if suburb_avg_yield > 0 else None
            result["yield_index"] = round(yield_index, 2) if yield_index else None
            result["yield_rating"] = _yield_rating(yield_index)

    return result


async def _search_rentals_tavily(location: str, bedrooms: int | None, property_type: str) -> dict:
    """Use Tavily to find rental listing prices."""
    from app.agents.tools.web_search import search_web

    bed_str = f"{bedrooms} bedroom " if bedrooms else ""
    type_str = f"{property_type} " if property_type != "any" else ""
    query = f"{bed_str}{type_str}rental price per week {location} site:domain.com.au OR site:realestate.com.au"

    results = await search_web(query, num_results=10)
    weekly_rents = []

    for r in results.get("results", []):
        snippet = r.get("snippet", "") + " " + r.get("title", "")
        rents = _extract_weekly_rents(snippet)
        weekly_rents.extend(rents)

    # Also try direct Domain rental scrape
    domain_rents = await _scrape_domain_rentals(location, bedrooms, property_type)
    weekly_rents.extend(domain_rents)

    # Filter outliers (remove top/bottom 10% if enough data)
    weekly_rents = [r for r in weekly_rents if 100 <= r <= 10000]
    if len(weekly_rents) >= 6:
        weekly_rents.sort()
        cut = max(1, len(weekly_rents) // 10)
        weekly_rents = weekly_rents[cut:-cut]

    return {"weekly_rents": weekly_rents}


async def _scrape_domain_rentals(location: str, bedrooms: int | None, property_type: str) -> list[int]:
    """Scrape Domain.com.au rental search results for weekly prices."""
    location_slug = location.lower().replace(" ", "-").replace(",", "")
    url = f"https://www.domain.com.au/rent/{location_slug}/"
    params = {}
    if bedrooms:
        params["bedrooms"] = f"{bedrooms}-any"

    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=20, follow_redirects=True) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return []

        soup = BeautifulSoup(resp.text, "lxml")
        prices = []
        for el in soup.select("[data-testid='listing-card-price'], .price, [class*='price']"):
            text = el.get_text(strip=True)
            rents = _extract_weekly_rents(text)
            prices.extend(rents)
        return prices[:30]
    except Exception as e:
        logger.debug(f"Domain rental scrape failed: {e}")
        return []


async def _search_sales_tavily(location: str, bedrooms: int | None, property_type: str) -> dict:
    """Use Tavily to find recent sale prices for yield index calculation."""
    from app.agents.tools.web_search import search_web

    bed_str = f"{bedrooms} bedroom " if bedrooms else ""
    type_str = f"{property_type} " if property_type != "any" else ""
    query = f"median {bed_str}{type_str}property price {location} 2024 2025"

    results = await search_web(query, num_results=8)
    sale_prices = []

    for r in results.get("results", []):
        snippet = r.get("snippet", "") + " " + r.get("title", "")
        prices = _extract_sale_prices(snippet)
        sale_prices.extend(prices)

    sale_prices = [p for p in sale_prices if 100_000 <= p <= 20_000_000]
    return {"sale_prices": sale_prices}


def _extract_weekly_rents(text: str) -> list[int]:
    """Extract $/week or pw figures from text."""
    rents = []
    # Match patterns like "$650/week", "$650pw", "$650 per week", "650pw"
    patterns = [
        r'\$\s*(\d{3,4})\s*(?:/\s*week|pw|per\s*week)',
        r'(\d{3,4})\s*(?:per\s*week|/week|pw)',
    ]
    for pattern in patterns:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            val = int(m.group(1))
            if 100 <= val <= 5000:
                rents.append(val)
    return rents


def _extract_sale_prices(text: str) -> list[int]:
    """Extract property sale prices from text (e.g. $750,000 or $1.2m)."""
    prices = []
    # Match $750,000 or $750k or $1.2m style
    for m in re.finditer(r'\$\s*([\d,]+(?:\.\d+)?)\s*(k|m|million)?', text, re.IGNORECASE):
        raw = m.group(1).replace(",", "")
        suffix = (m.group(2) or "").lower()
        try:
            val = float(raw)
            if suffix in ("m", "million"):
                val *= 1_000_000
            elif suffix == "k":
                val *= 1_000
            if 100_000 <= val <= 20_000_000:
                prices.append(int(val))
        except ValueError:
            pass
    return prices


def _yield_rating(yield_index: float | None) -> str:
    if yield_index is None:
        return "unknown"
    if yield_index >= 1.2:
        return "strong"      # 20%+ above suburb average
    if yield_index >= 1.05:
        return "above_average"
    if yield_index >= 0.95:
        return "average"
    if yield_index >= 0.80:
        return "below_average"
    return "weak"


GET_RENTAL_ESTIMATE_TOOL_DEF = {
    "name": "get_rental_estimate",
    "description": (
        "Estimate the rental yield for a property by finding comparable rental listings "
        "in the same suburb. Returns: median weekly rent, rental yield %, suburb average yield %, "
        "and yield index (>1.0 means this property yields above the suburb average). "
        "Call this for each listing AFTER you have the purchase price."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "Suburb and state, e.g. 'Newtown NSW' or 'Marrickville NSW'",
            },
            "bedrooms": {
                "type": "integer",
                "description": "Number of bedrooms (for comparable rental search)",
            },
            "property_type": {
                "type": "string",
                "enum": ["house", "apartment", "townhouse", "any"],
                "default": "any",
            },
            "purchase_price": {
                "type": "integer",
                "description": "The listing's purchase price in dollars (no commas), used to calculate yield",
            },
        },
        "required": ["location"],
    },
}
