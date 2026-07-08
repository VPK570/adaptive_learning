"""SurrealDB client — vector storage only (RAG embeddings)."""
import asyncio
import logging
from typing import Optional
from surrealdb import AsyncSurreal
from app.config import settings

logger = logging.getLogger(__name__)

_CONNECT_MAX_RETRIES = 5
_CONNECT_RETRY_DELAY = 2.0
_CONNECT_TIMEOUT = 10.0


class SurrealDBManager:
    _instance: Optional[AsyncSurreal] = None
    _lock = asyncio.Lock()

    @classmethod
    async def get_db(cls) -> AsyncSurreal:
        async with cls._lock:
            if cls._instance is not None:
                return cls._instance

            last_error: Optional[Exception] = None
            for attempt in range(1, _CONNECT_MAX_RETRIES + 1):
                try:
                    instance = await cls._connect_once()
                    cls._instance = instance
                    logger.info("Connected to SurrealDB (attempt %d)", attempt)
                    return cls._instance
                except Exception as e:
                    last_error = e
                    logger.warning(
                        "SurrealDB connection attempt %d/%d failed: %s",
                        attempt, _CONNECT_MAX_RETRIES, e,
                    )
                    cls._instance = None
                    if attempt < _CONNECT_MAX_RETRIES:
                        await asyncio.sleep(_CONNECT_RETRY_DELAY)

            raise ConnectionError(
                f"Could not connect to SurrealDB at {settings.SURREAL_URL} "
                f"after {_CONNECT_MAX_RETRIES} attempts"
            ) from last_error

    @classmethod
    async def _connect_once(cls) -> AsyncSurreal:
        async def _do_connect() -> AsyncSurreal:
            logger.info("Creating SurrealDB instance: url=%s ns=%s db=%s",
                        settings.SURREAL_URL, settings.SURREAL_NS, settings.SURREAL_DB)
            instance = AsyncSurreal(settings.SURREAL_URL)
            await instance.connect()
            await instance.signin({
                "user": settings.SURREAL_USER,
                "pass": settings.SURREAL_PASS,
            })
            await instance.use(settings.SURREAL_NS, settings.SURREAL_DB)
            await cls._init_schema(instance)
            logger.info("SurrealDB schema initialization completed")
            return instance

        return await asyncio.wait_for(_do_connect(), timeout=_CONNECT_TIMEOUT)

    @classmethod
    async def health_check(cls) -> bool:
        try:
            db = await cls.get_db()
            await db.query("INFO FOR DB")
            return True
        except Exception as e:
            logger.error("SurrealDB health check failed: %s", e)
            return False

    @classmethod
    async def reset(cls) -> None:
        async with cls._lock:
            if cls._instance is not None:
                try:
                    await cls._instance.close()
                    logger.info("Closed stale SurrealDB instance")
                except Exception as e:
                    logger.warning("Error closing stale SurrealDB instance: %s", e)
                cls._instance = None

    @classmethod
    async def _init_schema(cls, db: AsyncSurreal):
        schema_query = """
            DEFINE TABLE IF NOT EXISTS text_chunk SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS course_code ON TABLE text_chunk TYPE string;
            DEFINE FIELD IF NOT EXISTS text ON TABLE text_chunk TYPE string;
            DEFINE FIELD IF NOT EXISTS embedding ON TABLE text_chunk TYPE array<float>;
            DEFINE FIELD IF NOT EXISTS source_title ON TABLE text_chunk TYPE string;
            DEFINE FIELD IF NOT EXISTS topic ON TABLE text_chunk TYPE string;
            DEFINE FIELD IF NOT EXISTS page ON TABLE text_chunk TYPE number;
            DEFINE FIELD IF NOT EXISTS content_type ON TABLE text_chunk TYPE string;

            DEFINE ANALYZER IF NOT EXISTS chunk_analyzer TOKENIZERS blank,punct FILTERS lowercase,snowball(english);
            DEFINE INDEX IF NOT EXISTS text_search_idx ON TABLE text_chunk FIELDS text FULLTEXT ANALYZER chunk_analyzer BM25;
            DEFINE INDEX IF NOT EXISTS text_embedding_idx ON TABLE text_chunk FIELDS embedding HNSW DIMENSION 2048 DIST COSINE;

            DEFINE TABLE IF NOT EXISTS image_chunk SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS course_code ON TABLE image_chunk TYPE string;
            DEFINE FIELD IF NOT EXISTS text ON TABLE image_chunk TYPE string;
            DEFINE FIELD IF NOT EXISTS embedding ON TABLE image_chunk TYPE array<float>;
            DEFINE FIELD IF NOT EXISTS source_title ON TABLE image_chunk TYPE string;
            DEFINE FIELD IF NOT EXISTS topic ON TABLE image_chunk TYPE string;
            DEFINE FIELD IF NOT EXISTS page ON TABLE image_chunk TYPE number;
            DEFINE FIELD IF NOT EXISTS content_type ON TABLE image_chunk TYPE string;
            DEFINE FIELD IF NOT EXISTS mime_type ON TABLE image_chunk TYPE string;
            DEFINE FIELD IF NOT EXISTS image_size_kb ON TABLE image_chunk TYPE number;

            DEFINE INDEX IF NOT EXISTS image_embedding_idx ON TABLE image_chunk FIELDS embedding HNSW DIMENSION 2048 DIST COSINE;

            DEFINE TABLE IF NOT EXISTS curriculum_chunk SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS course_code ON TABLE curriculum_chunk TYPE string;
            DEFINE FIELD IF NOT EXISTS source_title ON TABLE curriculum_chunk TYPE string;
            DEFINE FIELD IF NOT EXISTS text ON TABLE curriculum_chunk TYPE string;
            DEFINE FIELD IF NOT EXISTS embedding ON TABLE curriculum_chunk TYPE array<float>;
            DEFINE FIELD IF NOT EXISTS topic ON TABLE curriculum_chunk TYPE string;
            DEFINE FIELD IF NOT EXISTS page ON TABLE curriculum_chunk TYPE number;
            DEFINE FIELD IF NOT EXISTS content_type ON TABLE curriculum_chunk TYPE string;

            DEFINE INDEX IF NOT EXISTS curriculum_embedding_idx ON TABLE curriculum_chunk FIELDS embedding HNSW DIMENSION 2048 DIST COSINE;

            DEFINE TABLE IF NOT EXISTS course SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS course_code ON TABLE course TYPE string;
            DEFINE FIELD IF NOT EXISTS course_name ON TABLE course TYPE string;
            DEFINE FIELD IF NOT EXISTS description ON TABLE course TYPE string;
            DEFINE FIELD IF NOT EXISTS icon ON TABLE course TYPE string;
            DEFINE FIELD IF NOT EXISTS created_at ON TABLE course TYPE datetime DEFAULT time::now();
            DEFINE INDEX IF NOT EXISTS course_code_idx ON TABLE course FIELDS course_code UNIQUE;

            DEFINE TABLE IF NOT EXISTS document SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS course_code ON TABLE document TYPE string;
            DEFINE FIELD IF NOT EXISTS filename ON TABLE document TYPE string;
            DEFINE FIELD IF NOT EXISTS content_hash ON TABLE document TYPE string;
            DEFINE FIELD IF NOT EXISTS created_at ON TABLE document TYPE string;
            DEFINE INDEX IF NOT EXISTS content_hash_idx ON TABLE document FIELDS content_hash UNIQUE;

            DEFINE INDEX IF NOT EXISTS text_chunk_course_idx ON TABLE text_chunk FIELDS course_code;
            DEFINE INDEX IF NOT EXISTS image_chunk_course_idx ON TABLE image_chunk FIELDS course_code;
            DEFINE INDEX IF NOT EXISTS curriculum_chunk_course_idx ON TABLE curriculum_chunk FIELDS course_code;

            DEFINE EVENT IF NOT EXISTS course_cascade_delete ON TABLE course WHEN $event = "DELETE" THEN {
                DELETE text_chunk WHERE course_code = $before.course_code;
                DELETE image_chunk WHERE course_code = $before.course_code;
                DELETE curriculum_chunk WHERE course_code = $before.course_code;
            };
        """
        try:
            await db.query(schema_query)
            logger.info("Schema initialized")
        except Exception as e:
            error_msg = str(e).lower()
            if "already exists" in error_msg or "duplicate" in error_msg:
                logger.info("Schema already exists: %s", e)
            else:
                logger.error("Schema init error: %s", e)
                raise


async def get_db():
    return await SurrealDBManager.get_db()


async def close_db():
    await SurrealDBManager.reset()
