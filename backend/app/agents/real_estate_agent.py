"""Real estate monitoring agent with rental yield analysis."""
from app.agents.base_agent import BaseAgent, REPORT_FINDING_TOOL_DEF
from app.agents.tools.web_search import SEARCH_WEB_TOOL_DEF
from app.agents.tools.web_scraper import SCRAPE_PAGE_TOOL_DEF
from app.agents.tools.real_estate import SEARCH_REAL_ESTATE_TOOL_DEF
from app.agents.tools.rental import GET_RENTAL_ESTIMATE_TOOL_DEF


class RealEstateAgent(BaseAgent):
    AGENT_TYPE = "real_estate"

    def get_tools(self) -> list[dict]:
        return [
            SEARCH_REAL_ESTATE_TOOL_DEF,
            GET_RENTAL_ESTIMATE_TOOL_DEF,
            SCRAPE_PAGE_TOOL_DEF,
            SEARCH_WEB_TOOL_DEF,
            REPORT_FINDING_TOOL_DEF,
        ]

    def get_system_prompt(self) -> str:
        return """You are a real estate monitoring and investment analysis agent. Your job is to find property listings matching the user's criteria AND analyse their investment potential via rental yield.

## Process

**Step 1 — Find listings**
- Use search_real_estate for each configured source and location
- For listings with limited info, use scrape_page to get full details
- Evaluate against ALL criteria: price range, bedrooms, property type, keywords

**Step 2 — Rental yield analysis (for each qualifying listing)**
- Call get_rental_estimate with the listing's location, bedrooms, property_type, and purchase_price
- This returns: median weekly rent, rental yield %, suburb avg yield %, yield index
- Yield index >1.0 = above suburb average, <1.0 = below average

**Step 3 — Report findings**
- Only call report_finding for listings that match the purchase criteria
- Include yield data in the metadata
- Set relevance_score based on BOTH criteria match AND yield quality:
  - 1.0 = perfect criteria match + strong yield (index ≥ 1.2)
  - 0.9 = perfect criteria match + average yield
  - 0.8 = good criteria match regardless of yield
  - below 0.7 = skip

## Metadata to include in report_finding
```json
{
  "price": "$750,000",
  "bedrooms": 3,
  "bathrooms": 2,
  "parking": 1,
  "location": "Newtown NSW",
  "property_type": "house",
  "estimated_weekly_rent": 650,
  "annual_rental_income": 33800,
  "rental_yield_pct": 4.51,
  "suburb_avg_yield_pct": 3.8,
  "yield_index": 1.19,
  "yield_rating": "above_average"
}
```

## Yield ratings
- strong: yield index ≥ 1.2 (20%+ above suburb average)
- above_average: 1.05–1.2
- average: 0.95–1.05
- below_average: 0.8–0.95
- weak: < 0.8

Be thorough. Every qualifying listing should have yield analysis before being reported."""

    def get_initial_message(self) -> str:
        c = self.criteria
        locations = c.get("locations", ["Unknown"])
        property_types = c.get("property_types", ["any"])
        price_min = c.get("price_min")
        price_max = c.get("price_max")
        bedrooms_min = c.get("bedrooms_min")
        bathrooms_min = c.get("bathrooms_min")
        keywords_include = c.get("keywords_include", [])
        keywords_exclude = c.get("keywords_exclude", [])
        sources = c.get("sources", ["domain.com.au", "realestate.com.au"])
        max_results = c.get("max_results", 20)
        min_rental_yield = c.get("min_rental_yield")
        min_yield_index = c.get("min_yield_index")

        price_str = ""
        if price_min and price_max:
            price_str = f"${price_min:,} - ${price_max:,}"
        elif price_min:
            price_str = f"from ${price_min:,}"
        elif price_max:
            price_str = f"up to ${price_max:,}"

        yield_str = ""
        if min_rental_yield:
            yield_str = f"\n**Minimum rental yield:** {min_rental_yield}%"
        if min_yield_index:
            yield_str += f"\n**Minimum yield index:** {min_yield_index} (vs suburb average)"

        return f"""Please search for property listings matching these criteria and analyse each one's rental yield:

**Locations:** {', '.join(locations)}
**Property Types:** {', '.join(property_types)}
**Price Range:** {price_str or 'Any'}
**Bedrooms:** {f'minimum {bedrooms_min}' if bedrooms_min else 'Any'}
**Bathrooms:** {f'minimum {bathrooms_min}' if bathrooms_min else 'Any'}
**Must include keywords:** {', '.join(keywords_include) if keywords_include else 'None'}
**Exclude if contains:** {', '.join(keywords_exclude) if keywords_exclude else 'None'}
**Search sources:** {', '.join(sources)}
**Max results to report:** {max_results}{yield_str}

For each qualifying listing:
1. Search the source for listings
2. Call get_rental_estimate to calculate rental yield and suburb yield index
3. Report via report_finding with full yield metadata

Prioritise listings with yield index > 1.0 (above suburb average)."""
