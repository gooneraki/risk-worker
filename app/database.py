"""Database configuration and session management"""
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

from app.config import settings

logger = logging.getLogger(__name__)

# Database setup
# DATABASE_URL is automatically converted to use async driver (postgresql+asyncpg://)
# if it starts with postgresql:// (common in production environments like Render.com)
DATABASE_URL = settings.database_url

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    poolclass=NullPool,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

logger.info("Database engine configured: %s",
            DATABASE_URL.split('@')[0] + '@***')


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Database session dependency"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("Database tables initialized")
    except Exception as e:
        logger.error("Failed to initialize database tables: %s", e)
        raise
