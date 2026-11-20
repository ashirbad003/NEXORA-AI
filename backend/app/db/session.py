from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
from sqlalchemy.orm import declarative_base
from backend.app.core.config import settings
from backend.app.core.logging import logger

def get_engine_args():
    url = settings.DATABASE_URL
    if url.startswith("sqlite"):
        return {
            "echo": settings.APP_DEBUG,
            "future": True,
            # NullPool for SQLite async avoids cross-thread event loop lock conflicts
            "poolclass": NullPool,
        }
    elif url.startswith("postgresql+asyncpg"):
        return {
            "echo": settings.APP_DEBUG,
            "future": True,
            "poolclass": AsyncAdaptedQueuePool,
            "pool_size": 10,
            "max_overflow": 20,
            "pool_timeout": 30,
            "pool_pre_ping": True,
            "pool_recycle": 1800,
        }
    else:
        # Strict validation: prevent silent fallback to misconfigured or insecure dialects
        raise ValueError(
            f"Unsupported or invalid DATABASE_URL dialect: '{url.split('://')[0]}'. "
            "Production requires 'postgresql+asyncpg://', isolated test suites require 'sqlite+aiosqlite://'."
        )

# Create async engine with validated configuration
engine = create_async_engine(settings.DATABASE_URL, **get_engine_args())

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()
