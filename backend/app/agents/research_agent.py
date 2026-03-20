"""General web research agent."""
from app.agents.base_agent import BaseAgent
from app.agents.tools.web_search import SEARCH_WEB_TOOL_DEF
from app.agents.tools.web_scraper import SCRAPE_PAGE_TOOL_DEF
from app.agents.base_agent import REPORT_FINDING_TOOL_DEF


class ResearchAgent(BaseAgent):
    AGENT_TYPE = "research"

    def get_tools(self) -> list[dict]:
        return [
            SEARCH_WEB_TOOL_DEF,
            SCRAPE_PAGE_TOOL_DEF,
            REPORT_FINDING_TOOL_DEF,
        ]

    def get_system_prompt(self) -> str:
        return """You are a web research agent. Your job is to research a topic thoroughly and report significant findings using the report_finding tool.

Process:
1. Start with a broad search_web query on the main topic
2. Identify the most relevant URLs from search results
3. Use scrape_page to get full content from the most relevant pages
4. Synthesize information and identify key insights, facts, or developments
5. Report each distinct significant finding using report_finding
6. Continue searching to find more angles if needed
7. Provide a final summary of what you learned

When reporting findings:
- finding_type: "research_result" for general insights, "alert" for important breaking news
- relevance_score: 1.0 = directly answers the query, 0.7 = tangentially related
- metadata: include source_domain, published_date if available, key_facts as a list

Be thorough and report multiple distinct findings rather than one big summary."""

    def get_initial_message(self) -> str:
        c = self.criteria
        query = c.get("query", "")
        search_depth = c.get("search_depth", "standard")
        max_sources = c.get("max_sources", 10)
        output_format = c.get("output_format", "summary")
        domains_include = c.get("domains_include", [])
        domains_exclude = c.get("domains_exclude", [])

        domain_instructions = ""
        if domains_include:
            domain_instructions += f"\nFocus on these domains: {', '.join(domains_include)}"
        if domains_exclude:
            domain_instructions += f"\nAvoid these domains: {', '.join(domains_exclude)}"

        return f"""Please research the following topic:

**Query:** {query}
**Search depth:** {search_depth} ({"go deep and follow links to source material" if search_depth == "deep" else "standard breadth search"})
**Maximum sources to use:** {max_sources}
**Output format:** {output_format}
{domain_instructions}

Search thoroughly, read key pages, and report each significant finding using report_finding. Aim for high-quality, distinct findings."""
