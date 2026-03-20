"""Real estate monitoring agent."""
import json
from typing import Any, Callable
from app.agents.base_agent import BaseAgent
from app.agents.tools.web_search import SEARCH_WEB_TOOL_DEF
from app.agents.tools.web_scraper import SCRAPE_PAGE_TOOL_DEF
from app.agents.tools.real_estate import SEARCH_REAL_ESTATE_TOOL_DEF
from app.agents.base_agent import REPORT_FINDING_TOOL_DEF


class RealEstateAgent(BaseAgent):
    AGENT_TYPE = "real_estate"

    def get_tools(self) -> list[dict]:
        return [
            SEARCH_REAL_ESTATE_TOOL_DEF,
            SCRAPE_PAGE_TOOL_DEF,
            SEARCH_WEB_TOOL_DEF,
            REPORT_FINDING_TOOL_DEF,
        ]

    def get_system_prompt(self) -> str:
        return """You are a real estate monitoring agent. Your job is to find property listings that match the user's criteria and report each matching one using the report_finding tool.

Process:
1. Use search_real_estate to query each configured source and location combination
2. For promising listings with limited info, use scrape_page to get full details
3. Evaluate each listing strictly against ALL criteria: price range, bedrooms, property type, keywords
4. Call report_finding ONLY for listings that genuinely match — quality over quantity
5. Assign relevance_score: 1.0 = perfect match on all criteria, 0.8+ = minor misses, below 0.7 = skip
6. After searching all sources, provide a brief summary of what you found

When reporting a finding, set metadata with: price (string), bedrooms (number), bathrooms (number), parking (number), location (string), property_type (string).

Be thorough but precise. If a listing is missing key criteria fields, use scrape_page to get more details before deciding."""

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

        price_str = ""
        if price_min and price_max:
            price_str = f"${price_min:,} - ${price_max:,}"
        elif price_min:
            price_str = f"from ${price_min:,}"
        elif price_max:
            price_str = f"up to ${price_max:,}"

        return f"""Please search for property listings matching these criteria:

**Locations:** {', '.join(locations)}
**Property Types:** {', '.join(property_types)}
**Price Range:** {price_str or 'Any'}
**Bedrooms:** {f'minimum {bedrooms_min}' if bedrooms_min else 'Any'}
**Bathrooms:** {f'minimum {bathrooms_min}' if bathrooms_min else 'Any'}
**Must include keywords:** {', '.join(keywords_include) if keywords_include else 'None'}
**Exclude if contains:** {', '.join(keywords_exclude) if keywords_exclude else 'None'}
**Search sources:** {', '.join(sources)}
**Max results to report:** {max_results}

Search each location on each source. Report each matching listing using report_finding. Be thorough."""
