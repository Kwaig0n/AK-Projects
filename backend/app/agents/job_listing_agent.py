"""Job listing scanner agent — searches Seek/LinkedIn/Indeed and scores against a CV."""
from app.agents.base_agent import BaseAgent, REPORT_FINDING_TOOL_DEF
from app.agents.tools.web_scraper import SCRAPE_PAGE_TOOL_DEF
from app.agents.tools.job_search import SEARCH_JOBS_TOOL_DEF


class JobListingAgent(BaseAgent):
    AGENT_TYPE = "job_listing"

    def get_tools(self) -> list[dict]:
        return [
            SEARCH_JOBS_TOOL_DEF,
            SCRAPE_PAGE_TOOL_DEF,
            *self._get_skill_tools(),
            REPORT_FINDING_TOOL_DEF,
        ]

    def get_system_prompt(self) -> str:
        return """You are a job listing scanner. Your job is to find relevant job postings, scrape their full descriptions, score them against the user's CV, and report strong matches.

## Process

**Step 1 — Search each source**
- Call search_jobs for each combination of job title + location + source in the criteria
- You may get duplicates across sources — track URLs you've already processed

**Step 2 — Scrape and evaluate**
- For each promising result from the search, call scrape_page to get the full job description
- Evaluate each listing against ALL criteria:
  - Does the job title / seniority level match?
  - Do the required skills overlap with the CV?
  - Is the location acceptable (including remote options)?
  - Are salary expectations met (if listed)?
  - Do keywords_include appear in the description?
  - Do keywords_exclude disqualify it?

**Step 3 — Score and report**
- Assign a cv_match_score (0.0–1.0):
  - 1.0 = perfect role, all skills match, great location/salary
  - 0.85 = strong match, minor gaps
  - 0.70 = decent match, some missing skills but learnable
  - below 0.70 = skip (unless min_match_score is set lower)
- Only report findings that meet or exceed min_match_score
- Call report_finding once per qualifying job

## Metadata to include in report_finding
```json
{
  "company": "Acme Corp",
  "job_title": "Senior Python Developer",
  "location": "Sydney CBD (Hybrid)",
  "employment_type": "full_time",
  "salary": "$130,000 - $150,000",
  "source": "seek.com.au",
  "posted_date": "2 days ago",
  "cv_match_score": 0.87,
  "matching_skills": ["Python", "FastAPI", "PostgreSQL"],
  "missing_skills": ["Kubernetes"],
  "match_reasoning": "Strong Python/FastAPI background aligns well. Kubernetes is listed as 'nice to have'."
}
```

## Important notes
- Set finding_type to "job_listing"
- Set relevance_score equal to cv_match_score
- Be precise in match_reasoning — tell the user exactly why this is a good fit
- Stop once you've found and reported max_results qualifying listings
- Avoid reporting the same URL twice"""

    def get_initial_message(self) -> str:
        c = self.criteria
        job_titles = c.get("job_titles", ["Software Engineer"])
        locations = c.get("locations", ["Remote"])
        sources = c.get("sources", ["seek.com.au", "linkedin.com"])
        keywords_include = c.get("keywords_include", [])
        keywords_exclude = c.get("keywords_exclude", [])
        min_match_score = c.get("min_match_score", 0.70)
        salary_min = c.get("salary_min")
        salary_max = c.get("salary_max")
        employment_type = c.get("employment_type", "any")
        max_results = c.get("max_results", 10)
        cv_summary = c.get("cv_summary", "No CV provided — score based on job title and keyword matches only.")

        salary_str = ""
        if salary_min and salary_max:
            salary_str = f"${salary_min:,} – ${salary_max:,}"
        elif salary_min:
            salary_str = f"from ${salary_min:,}"
        elif salary_max:
            salary_str = f"up to ${salary_max:,}"

        return f"""Please search for job listings matching my criteria, scrape the full descriptions, and score each against my CV.

**Job titles to search:** {', '.join(job_titles)}
**Locations:** {', '.join(locations)}
**Employment type:** {employment_type}
**Salary range:** {salary_str or 'Any'}
**Sources to search:** {', '.join(sources)}
**Must include keywords:** {', '.join(keywords_include) if keywords_include else 'None'}
**Exclude if contains:** {', '.join(keywords_exclude) if keywords_exclude else 'None'}
**Minimum CV match score:** {min_match_score}
**Max results to report:** {max_results}

**My CV / Skills Summary:**
{cv_summary}

For each result:
1. Search each source for each job title + location
2. Scrape the full job description from the listing URL
3. Score it against my CV and criteria
4. Report via report_finding if score ≥ {min_match_score}

Focus on quality over quantity — only report roles that are genuinely a strong fit."""
