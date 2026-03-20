from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path
import dotenv

# Always resolve .env relative to this file's location (backend/)
_ENV_FILE = Path(__file__).parent.parent / ".env"

# Load into os.environ so pydantic-settings picks them up reliably
dotenv.load_dotenv(_ENV_FILE, override=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    # Claude
    anthropic_api_key: str = ""

    # Web Search
    tavily_api_key: str = ""

    # Telegram
    telegram_bot_token: str = ""
    telegram_default_chat_id: str = ""

    # Database
    database_url: str = "sqlite+aiosqlite:///./agents.db"

    # App
    environment: str = "development"
    frontend_url: str = "http://localhost:3000"
    secret_key: str = "change-me-in-production"

    # Agent limits
    max_agent_iterations: int = 8
    agent_request_delay_seconds: float = 1.0


settings = Settings()
