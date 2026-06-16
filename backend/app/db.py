"""SurrealDB client — unified storage for vectors and documents."""

import asyncio
import logging
from typing import Optional
from surrealdb import AsyncSurreal
from app.config import settings

logger = logging.getLogger(__name__)

# Connection retry configuration
_CONNECT_MAX_RETRIES = 5
_CONNECT_RETRY_DELAY = 2.0  # seconds between attempts
_CONNECT_TIMEOUT = 10.0     # seconds per connection attempt


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
                    # Make sure we never cache a half-open instance
                    cls._instance = None
                    if attempt < _CONNECT_MAX_RETRIES:
                        await asyncio.sleep(_CONNECT_RETRY_DELAY)

            raise ConnectionError(
                f"Could not connect to SurrealDB at {settings.SURREAL_URL} "
                f"after {_CONNECT_MAX_RETRIES} attempts"
            ) from last_error

    @classmethod
    async def _connect_once(cls) -> AsyncSurreal:
        """Single connection attempt, bounded by a timeout."""
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

        # Bound the whole connect sequence so a hung connect can't block forever
        return await asyncio.wait_for(_do_connect(), timeout=_CONNECT_TIMEOUT)

    @classmethod
    async def reset(cls) -> None:
        """Drop the cached instance so the next get_db() reconnects.

        Useful after the database restarts and the old socket is dead.
        """
        async with cls._lock:
            if cls._instance is not None:
                try:
                    await cls._instance.close()
                except Exception as e:
                    logger.warning("Error closing stale SurrealDB instance: %s", e)
                cls._instance = None

    @classmethod
    async def _init_schema(cls, db: AsyncSurreal):
        """Initialize SurrealDB schema."""
        # Simple schema for testing/base
        schema_query = """
            DEFINE TABLE IF NOT EXISTS text_chunk SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS course_code ON TABLE text_chunk TYPE string;
            DEFINE FIELD IF NOT EXISTS text ON TABLE text_chunk TYPE string;
            DEFINE FIELD IF NOT EXISTS embedding ON TABLE text_chunk TYPE array<float>;
            DEFINE FIELD IF NOT EXISTS source_title ON TABLE text_chunk TYPE string;
            DEFINE FIELD IF NOT EXISTS topic ON TABLE text_chunk TYPE string;
            DEFINE FIELD IF NOT EXISTS page ON TABLE text_chunk TYPE number;
            DEFINE FIELD IF NOT EXISTS content_type ON TABLE text_chunk TYPE string;

            -- Full-Text Search Index
            DEFINE ANALYZER IF NOT EXISTS chunk_analyzer TOKENIZERS blank,punct FILTERS lowercase,snowball(english);
            DEFINE INDEX IF NOT EXISTS text_search_idx ON TABLE text_chunk FIELDS text FULLTEXT ANALYZER chunk_analyzer BM25;

            -- Vector Indexes
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

            DEFINE TABLE IF NOT EXISTS chat_history SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS course_code ON TABLE chat_history TYPE string;
            DEFINE FIELD IF NOT EXISTS session_id ON TABLE chat_history TYPE string;
            DEFINE FIELD IF NOT EXISTS role ON TABLE chat_history TYPE string;
            DEFINE FIELD IF NOT EXISTS content ON TABLE chat_history TYPE string;
            DEFINE FIELD IF NOT EXISTS timestamp ON TABLE chat_history TYPE string;

            DEFINE TABLE IF NOT EXISTS flashcard_set SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS course_code ON TABLE flashcard_set TYPE string;
            DEFINE FIELD IF NOT EXISTS title ON TABLE flashcard_set TYPE string;
            DEFINE FIELD IF NOT EXISTS flashcards ON TABLE flashcard_set TYPE array;
            DEFINE FIELD IF NOT EXISTS created_at ON TABLE flashcard_set TYPE string;

            DEFINE TABLE IF NOT EXISTS quiz SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS course_code ON TABLE quiz TYPE string;
            DEFINE FIELD IF NOT EXISTS title ON TABLE quiz TYPE string;
            DEFINE FIELD IF NOT EXISTS questions ON TABLE quiz TYPE array;
            DEFINE FIELD IF NOT EXISTS created_at ON TABLE quiz TYPE string;

            DEFINE TABLE IF NOT EXISTS query_log SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS course_code ON TABLE query_log TYPE string;
            DEFINE FIELD IF NOT EXISTS question ON TABLE query_log TYPE string;
            DEFINE FIELD IF NOT EXISTS response_preview ON TABLE query_log TYPE string;
            DEFINE FIELD IF NOT EXISTS timestamp ON TABLE query_log TYPE string;
            DEFINE FIELD IF NOT EXISTS out_of_scope ON TABLE query_log TYPE bool;
            DEFINE FIELD IF NOT EXISTS cited_sources ON TABLE query_log TYPE array;

            -- Indexes on course_code: nearly every query filters by course_code,
            -- so these turn full-table scans into fast indexed lookups.
            DEFINE INDEX IF NOT EXISTS chat_history_course_idx ON TABLE chat_history FIELDS course_code;
            DEFINE INDEX IF NOT EXISTS query_log_course_idx ON TABLE query_log FIELDS course_code;
            DEFINE INDEX IF NOT EXISTS flashcard_set_course_idx ON TABLE flashcard_set FIELDS course_code;
            DEFINE INDEX IF NOT EXISTS quiz_course_idx ON TABLE quiz FIELDS course_code;
            DEFINE INDEX IF NOT EXISTS text_chunk_course_idx ON TABLE text_chunk FIELDS course_code;
            DEFINE INDEX IF NOT EXISTS image_chunk_course_idx ON TABLE image_chunk FIELDS course_code;
            DEFINE INDEX IF NOT EXISTS curriculum_chunk_course_idx ON TABLE curriculum_chunk FIELDS course_code;
            DEFINE TABLE IF NOT EXISTS users SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS email ON TABLE users TYPE string;
            DEFINE FIELD IF NOT EXISTS hashed_password ON TABLE users TYPE string;
            DEFINE FIELD IF NOT EXISTS role ON TABLE users TYPE string;
            DEFINE FIELD IF NOT EXISTS created_at ON TABLE users TYPE string;
            DEFINE INDEX IF NOT EXISTS users_email_idx ON TABLE users FIELDS email UNIQUE;
            DEFINE EVENT IF NOT EXISTS course_cascade_delete ON TABLE course WHEN $event = "DELETE" THEN {
            DELETE text_chunk WHERE course_code = $before.course_code;
            DELETE image_chunk WHERE course_code = $before.course_code;
            DELETE curriculum_chunk WHERE course_code = $before.course_code;
            };
        """
        try:
            logger.info("Executing schema initialization...")
            await db.query(schema_query)
            logger.info("Schema initialization completed successfully")
        except Exception as e:
            error_msg = str(e).lower()
            if "already exists" in error_msg or "duplicate" in error_msg:
                logger.info("Schema already exists: %s", e)
            else:
                logger.error("Schema initialization error: %s", e)
                raise


async def get_db():
    return await SurrealDBManager.get_db()


async def close_db():
    await SurrealDBManager.reset()