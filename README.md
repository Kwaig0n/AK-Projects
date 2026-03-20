# Agent Hub — AI Agent Ecosystem

A self-hosted AI agent ecosystem powered by Claude. Monitor real estate listings, run web research, and get notified via Telegram — all from a web dashboard.

## Features

- **Real Estate Agent** — monitors Domain.com.au and realestate.com.au for listings matching your custom criteria (price, bedrooms, location, keywords)
- **Research Agent** — web search and deep-read agent for any topic
- **Web Dashboard** — live run logs (SSE), findings browser, agent management
- **Telegram Bot** — trigger agents on demand, receive findings notifications
- **Scheduling** — cron-based automatic runs (e.g. every morning at 9am)
- **Extensible** — add new agent types by subclassing `BaseAgent`

## Setup

### 1. Get API Keys

You'll need:
- **Anthropic API key** — [console.anthropic.com](https://console.anthropic.com)
- **Tavily API key** — [tavily.com](https://tavily.com) (free tier available)
- **Telegram Bot Token** — message [@BotFather](https://t.me/BotFather) on Telegram and create a bot
- **Telegram Chat ID** — message [@userinfobot](https://t.me/userinfobot) to get your personal chat ID

### 2. Backend

```bash
cd backend
cp .env.example .env
# Edit .env with your API keys

pip3.12 install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be at `http://localhost:8000`. Swagger docs at `http://localhost:8000/docs`.

### 3. Frontend

```bash
cd frontend
# Edit .env.local if your backend runs on a different port
npm install
npm run dev
```

Dashboard at `http://localhost:3000`.

### 4. Telegram Bot

Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_DEFAULT_CHAT_ID` in `backend/.env`. The bot starts automatically when the backend starts.

Send `/start` to your bot to verify it's working.

## Usage

### Create your first agent

1. Open the dashboard → **New Agent**
2. Choose **Real Estate** type
3. Set criteria (locations, price range, bedrooms)
4. Optionally set a cron schedule (e.g. `0 9 * * *` for daily at 9am)
5. Click **Create Agent**

### Run on demand

- **Dashboard**: Click **Run Now** on any agent card
- **Telegram**: Send `/run <agent name>`

### Telegram Commands

```
/status           — All agents: name, last run, next run
/run <name>       — Trigger an agent
/results          — Latest findings (last 24h)
/criteria <name>  — Show agent search criteria
/history          — Last 10 runs
/pause <name>     — Pause scheduled runs
/resume <name>    — Resume scheduled runs
/help             — All commands
```

## Real Estate Criteria

```json
{
  "locations": ["Newtown NSW", "Marrickville NSW"],
  "property_types": ["apartment", "house", "townhouse"],
  "price_min": 500000,
  "price_max": 900000,
  "bedrooms_min": 2,
  "bathrooms_min": 1,
  "keywords_include": ["parking", "balcony"],
  "keywords_exclude": ["auction"],
  "sources": ["domain.com.au", "realestate.com.au"],
  "max_results": 20,
  "only_new_listings": true
}
```

## Research Criteria

```json
{
  "query": "AI startup funding rounds 2026",
  "search_depth": "deep",
  "max_sources": 10,
  "output_format": "summary",
  "domains_include": [],
  "domains_exclude": ["reddit.com"]
}
```

## Cron Examples

| Expression       | Meaning              |
|-----------------|----------------------|
| `0 9 * * *`     | Daily at 9am         |
| `0 9 * * 1-5`   | Weekdays at 9am      |
| `0 */4 * * *`   | Every 4 hours        |
| `0 9,18 * * *`  | 9am and 6pm daily    |
| `0 9 * * 1`     | Every Monday at 9am  |

## Project Structure

```
Agents/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + lifespan
│   │   ├── agents/              # Claude agent implementations
│   │   │   ├── base_agent.py    # Core agentic loop
│   │   │   ├── real_estate_agent.py
│   │   │   ├── research_agent.py
│   │   │   └── tools/           # search_web, scrape_page, search_real_estate
│   │   ├── api/                 # REST routes
│   │   ├── services/            # agent_service, sse_service, notifications
│   │   ├── scheduler/           # APScheduler
│   │   └── telegram/            # Bot commands
│   └── requirements.txt
└── frontend/                    # Next.js 16 dashboard
    └── app/
        ├── page.tsx             # Home dashboard
        ├── agents/              # Agent list, create, detail
        ├── runs/                # Run history + live log viewer
        └── findings/            # Findings browser
```
