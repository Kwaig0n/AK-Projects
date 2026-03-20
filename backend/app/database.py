from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def create_tables():
    async with engine.begin() as conn:
        from app.models import agent  # noqa: F401 — registers models with Base
        await conn.run_sync(Base.metadata.create_all)


async def migrate_db():
    """Add any missing columns to existing tables (safe to run on every startup)."""
    migrations = [
        "ALTER TABLE agent_configs ADD COLUMN enabled_skills TEXT DEFAULT '[]'",
    ]
    async with engine.begin() as conn:
        for stmt in migrations:
            try:
                await conn.execute(text(stmt))
            except Exception:
                pass  # Column already exists — safe to ignore
