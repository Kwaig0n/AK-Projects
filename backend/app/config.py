from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

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
    max_agent_iterations: int = 15
    agent_request_delay_seconds: float = 2.0


settings = Settings()
