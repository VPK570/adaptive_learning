import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

logger = logging.getLogger(__name__)

_CONNECT_MAX_RETRIES = 5
_CONNECT_RETRY_DELAY = 2.0
_POOL_PRE_PING = True


class Base(DeclarativeBase):
    pass


class Database:
    _engine = None
    _session_factory = None

    @classmethod
    def init(cls):
        url = settings.DATABASE_URL
        cls._engine = create_async_engine(
            url,
            echo=settings.DB_ECHO_SQL,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_pre_ping=_POOL_PRE_PING,
        )
        cls._session_factory = async_sessionmaker(
            cls._engine, expire_on_commit=False
        )
        logger.info(
            "Postgres engine created: pool_size=%s max_overflow=%s",
            settings.DB_POOL_SIZE, settings.DB_MAX_OVERFLOW,
        )

    @classmethod
    async def create_all(cls):
        async with cls._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Postgres tables created")

    @classmethod
    @asynccontextmanager
    async def session(cls) -> AsyncGenerator[AsyncSession, None]:
        if cls._session_factory is None:
            raise RuntimeError("Database not initialized. Call Database.init() first.")
        async with cls._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    @classmethod
    async def health_check(cls) -> bool:
        if cls._engine is None:
            return False
        try:
            async with cls._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error("Postgres health check failed: %s", e)
            return False

    @classmethod
    async def wait_ready(cls) -> bool:
        """Retry connection with backoff. Returns True if connected, False if all retries exhausted."""
        for attempt in range(1, _CONNECT_MAX_RETRIES + 1):
            ok = await cls.health_check()
            if ok:
                if attempt > 1:
                    logger.info("Postgres ready after %d attempts", attempt)
                return True
            logger.warning("Postgres not ready (attempt %d/%d)", attempt, _CONNECT_MAX_RETRIES)
            if attempt < _CONNECT_MAX_RETRIES:
                await asyncio.sleep(_CONNECT_RETRY_DELAY)
        logger.error("Postgres not reachable after %d attempts", _CONNECT_MAX_RETRIES)
        return False

    @classmethod
    async def close(cls):
        if cls._engine is not None:
            await cls._engine.dispose()
            cls._engine = None
            cls._session_factory = None
            logger.info("Postgres engine disposed")


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with Database.session() as session:
        yield session
