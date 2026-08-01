"""SurrealDB client — primary database for all persistence."""
import asyncio
import logging
from typing import Optional

from surrealdb import AsyncSurreal

from app.config import settings

logger = logging.getLogger(__name__)

_CONNECT_MAX_RETRIES = 5
_CONNECT_RETRY_DELAY = 2.0
_CONNECT_TIMEOUT = 30.0


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
    async def _probe_dimension(cls) -> int:
        from app.provider_router import router
        vector = await router.embed_text("probe")
        dim = len(vector)
        if not isinstance(dim, int) or dim < 64 or dim > 8192:
            raise RuntimeError(
                f"Embedding dimension probe returned {dim} — refusing to start. "
                f"Model: {settings.EMBEDDING_MODEL}"
            )
        logger.info("Embedding dimension probe: %d (model: %s)", dim, settings.EMBEDDING_MODEL)
        return dim

    @classmethod
    async def _init_schema(cls, db: AsyncSurreal):
        dim = await cls._probe_dimension()
        schema_query = f"""
            DEFINE TABLE IF NOT EXISTS text_chunk SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS course_code ON TABLE text_chunk TYPE string;
            DEFINE FIELD IF NOT EXISTS text ON TABLE text_chunk TYPE string;
            DEFINE FIELD IF NOT EXISTS embedding ON TABLE text_chunk TYPE array<float>;
            DEFINE FIELD IF NOT EXISTS source_title ON TABLE text_chunk TYPE string;
            DEFINE FIELD IF NOT EXISTS topic ON TABLE text_chunk TYPE string;
            DEFINE FIELD IF NOT EXISTS page ON TABLE text_chunk TYPE number;
            DEFINE FIELD IF NOT EXISTS content_type ON TABLE text_chunk TYPE string;
            REMOVE FIELD IF EXISTS section_heading ON TABLE text_chunk;
            DEFINE FIELD section_heading ON TABLE text_chunk TYPE option<string>;

            DEFINE ANALYZER IF NOT EXISTS chunk_analyzer TOKENIZERS blank,punct FILTERS lowercase,snowball(english);
            DEFINE INDEX IF NOT EXISTS text_search_idx ON TABLE text_chunk FIELDS text FULLTEXT ANALYZER chunk_analyzer BM25;
            DEFINE INDEX IF NOT EXISTS text_embedding_idx ON TABLE text_chunk FIELDS embedding HNSW DIMENSION {dim} DIST COSINE;

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

            DEFINE INDEX IF NOT EXISTS image_embedding_idx ON TABLE image_chunk FIELDS embedding HNSW DIMENSION {dim} DIST COSINE;

            DEFINE TABLE IF NOT EXISTS curriculum_chunk SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS course_code ON TABLE curriculum_chunk TYPE string;
            DEFINE FIELD IF NOT EXISTS source_title ON TABLE curriculum_chunk TYPE string;
            DEFINE FIELD IF NOT EXISTS text ON TABLE curriculum_chunk TYPE string;
            DEFINE FIELD IF NOT EXISTS embedding ON TABLE curriculum_chunk TYPE array<float>;
            DEFINE FIELD IF NOT EXISTS topic ON TABLE curriculum_chunk TYPE string;
            DEFINE FIELD IF NOT EXISTS page ON TABLE curriculum_chunk TYPE number;
            DEFINE FIELD IF NOT EXISTS content_type ON TABLE curriculum_chunk TYPE string;

            DEFINE INDEX IF NOT EXISTS curriculum_embedding_idx ON TABLE curriculum_chunk FIELDS embedding HNSW DIMENSION {dim} DIST COSINE;

            DEFINE TABLE IF NOT EXISTS course_topic SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS course_code ON TABLE course_topic TYPE string;
            DEFINE FIELD IF NOT EXISTS topic_name ON TABLE course_topic TYPE string;
            DEFINE FIELD IF NOT EXISTS subtopics ON TABLE course_topic TYPE array;
            DEFINE FIELD IF NOT EXISTS subtopics[*] ON TABLE course_topic TYPE string;
            DEFINE FIELD IF NOT EXISTS prerequisites ON TABLE course_topic TYPE array;
            DEFINE FIELD IF NOT EXISTS prerequisites[*] ON TABLE course_topic TYPE string;
            DEFINE FIELD IF NOT EXISTS bloom_level ON TABLE course_topic TYPE option<string>;
            DEFINE FIELD IF NOT EXISTS learning_objectives ON TABLE course_topic TYPE array;
            DEFINE FIELD IF NOT EXISTS learning_objectives[*] ON TABLE course_topic TYPE string;
            DEFINE FIELD IF NOT EXISTS order_index ON TABLE course_topic TYPE number;
            REMOVE FIELD IF EXISTS embedding ON TABLE course_topic;
            DEFINE FIELD embedding ON TABLE course_topic TYPE option<array>;
            DEFINE INDEX IF NOT EXISTS ct_course_topic_idx ON TABLE course_topic FIELDS course_code, topic_name UNIQUE;

            DEFINE TABLE IF NOT EXISTS course SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS course_code ON TABLE course TYPE string;
            DEFINE FIELD IF NOT EXISTS course_name ON TABLE course TYPE string;
            DEFINE FIELD IF NOT EXISTS description ON TABLE course TYPE string;
            DEFINE FIELD IF NOT EXISTS icon ON TABLE course TYPE string;
            DEFINE FIELD IF NOT EXISTS created_at ON TABLE course TYPE datetime DEFAULT time::now();
            DEFINE INDEX IF NOT EXISTS course_code_idx ON TABLE course FIELDS course_code UNIQUE;

            DEFINE TABLE IF NOT EXISTS document SCHEMAFULL;
            ALTER TABLE document SCHEMALESS;
            REMOVE FIELD IF EXISTS topic_analysis ON TABLE document;
            REMOVE FIELD IF EXISTS topic_analysis.topics ON TABLE document;
            REMOVE FIELD IF EXISTS topic_analysis.module_coverage ON TABLE document;
            REMOVE FIELD IF EXISTS topic_analysis.extra_topics ON TABLE document;
            REMOVE FIELD IF EXISTS topic_analysis.total_chunks ON TABLE document;
            REMOVE FIELD IF EXISTS topic_analysis.uncategorized_chunks ON TABLE document;
            DEFINE INDEX IF NOT EXISTS document_hash_idx ON TABLE document FIELDS course_code, content_hash UNIQUE;

            DEFINE TABLE IF NOT EXISTS user SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS user_id ON TABLE user TYPE string;
            DEFINE FIELD IF NOT EXISTS email ON TABLE user TYPE string;
            DEFINE FIELD IF NOT EXISTS hashed_password ON TABLE user TYPE string;
            DEFINE FIELD IF NOT EXISTS role ON TABLE user TYPE string;
            DEFINE FIELD IF NOT EXISTS name ON TABLE user TYPE string;
            DEFINE FIELD IF NOT EXISTS created_at ON TABLE user TYPE datetime DEFAULT time::now();
            DEFINE INDEX IF NOT EXISTS user_email_idx ON TABLE user FIELDS email UNIQUE;
            DEFINE INDEX IF NOT EXISTS user_user_id_idx ON TABLE user FIELDS user_id UNIQUE;

            DEFINE TABLE IF NOT EXISTS chat_message SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS user_id ON TABLE chat_message TYPE string;
            DEFINE FIELD IF NOT EXISTS course_code ON TABLE chat_message TYPE string;
            DEFINE FIELD IF NOT EXISTS session_id ON TABLE chat_message TYPE string;
            DEFINE FIELD IF NOT EXISTS message_role ON TABLE chat_message TYPE string;
            DEFINE FIELD IF NOT EXISTS content ON TABLE chat_message TYPE string;
            DEFINE FIELD IF NOT EXISTS timestamp ON TABLE chat_message TYPE datetime DEFAULT time::now();
            DEFINE INDEX IF NOT EXISTS chat_course_session_idx ON TABLE chat_message FIELDS course_code, session_id;

            DEFINE TABLE IF NOT EXISTS query_log SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS user_id ON TABLE query_log TYPE string;
            DEFINE FIELD IF NOT EXISTS course_code ON TABLE query_log TYPE string;
            DEFINE FIELD IF NOT EXISTS question ON TABLE query_log TYPE string;
            DEFINE FIELD IF NOT EXISTS response_preview ON TABLE query_log TYPE string;
            DEFINE FIELD IF NOT EXISTS out_of_scope ON TABLE query_log TYPE option<bool> DEFAULT false;
            DEFINE FIELD IF NOT EXISTS cited_sources ON TABLE query_log TYPE array;
            DEFINE FIELD IF NOT EXISTS cited_sources[*].source_title ON TABLE query_log TYPE string;
            DEFINE FIELD IF NOT EXISTS cited_sources[*].page ON TABLE query_log TYPE string;
            DEFINE FIELD IF NOT EXISTS cited_sources[*].content_type ON TABLE query_log TYPE string;
            DEFINE FIELD IF NOT EXISTS cited_sources[*].has_image ON TABLE query_log TYPE bool;
            DEFINE FIELD IF NOT EXISTS timestamp ON TABLE query_log TYPE datetime DEFAULT time::now();
            DEFINE INDEX IF NOT EXISTS query_log_course_idx ON TABLE query_log FIELDS course_code;

            DEFINE TABLE IF NOT EXISTS quiz SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS user_id ON TABLE quiz TYPE string;
            DEFINE FIELD IF NOT EXISTS course_code ON TABLE quiz TYPE string;
            DEFINE FIELD IF NOT EXISTS topic ON TABLE quiz TYPE string;
            DEFINE FIELD IF NOT EXISTS bloom_levels ON TABLE quiz TYPE array;
            DEFINE FIELD IF NOT EXISTS questions ON TABLE quiz TYPE any;
            DEFINE FIELD IF NOT EXISTS score ON TABLE quiz TYPE int;
            DEFINE FIELD IF NOT EXISTS total ON TABLE quiz TYPE int;
            DEFINE FIELD IF NOT EXISTS created_at ON TABLE quiz TYPE datetime DEFAULT time::now();
            DEFINE FIELD IF NOT EXISTS completed_at ON TABLE quiz TYPE datetime;
            DEFINE INDEX IF NOT EXISTS quiz_course_idx ON TABLE quiz FIELDS course_code;

            DEFINE TABLE IF NOT EXISTS flashcard_set SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS user_id ON TABLE flashcard_set TYPE string;
            DEFINE FIELD IF NOT EXISTS course_code ON TABLE flashcard_set TYPE string;
            DEFINE FIELD IF NOT EXISTS topic ON TABLE flashcard_set TYPE string;
            DEFINE FIELD IF NOT EXISTS bloom_level ON TABLE flashcard_set TYPE option<int>;
            DEFINE FIELD IF NOT EXISTS cards ON TABLE flashcard_set TYPE any;
            DEFINE FIELD IF NOT EXISTS created_at ON TABLE flashcard_set TYPE datetime DEFAULT time::now();
            DEFINE INDEX IF NOT EXISTS flashcard_course_idx ON TABLE flashcard_set FIELDS course_code;

            DEFINE INDEX IF NOT EXISTS text_chunk_course_idx ON TABLE text_chunk FIELDS course_code;
            DEFINE INDEX IF NOT EXISTS image_chunk_course_idx ON TABLE image_chunk FIELDS course_code;
            DEFINE INDEX IF NOT EXISTS curriculum_chunk_course_idx ON TABLE curriculum_chunk FIELDS course_code;

            DEFINE EVENT IF NOT EXISTS course_cascade_delete ON TABLE course WHEN $event = "DELETE" THEN {{
                DELETE text_chunk WHERE course_code = $before.course_code;
                DELETE image_chunk WHERE course_code = $before.course_code;
                DELETE curriculum_chunk WHERE course_code = $before.course_code;
                DELETE course_topic WHERE course_code = $before.course_code;
                DELETE knowledge_state WHERE course_code = $before.course_code;
                DELETE question_log WHERE course_code = $before.course_code;
                DELETE topic_prerequisite WHERE course_code = $before.course_code;
            }};

            DEFINE TABLE IF NOT EXISTS knowledge_state SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS student_id ON TABLE knowledge_state TYPE string;
            DEFINE FIELD IF NOT EXISTS course_code ON TABLE knowledge_state TYPE string;
            DEFINE FIELD IF NOT EXISTS topic_id ON TABLE knowledge_state TYPE string;
            DEFINE FIELD IF NOT EXISTS bloom_level ON TABLE knowledge_state TYPE int;
            DEFINE FIELD IF NOT EXISTS mastery_score ON TABLE knowledge_state TYPE float;
            DEFINE FIELD IF NOT EXISTS confidence ON TABLE knowledge_state TYPE float;
            DEFINE FIELD IF NOT EXISTS stability ON TABLE knowledge_state TYPE option<float>;
            DEFINE FIELD IF NOT EXISTS difficulty ON TABLE knowledge_state TYPE option<float>;
            DEFINE FIELD IF NOT EXISTS total_attempts ON TABLE knowledge_state TYPE int;
            DEFINE FIELD IF NOT EXISTS correct_attempts ON TABLE knowledge_state TYPE int;
            DEFINE FIELD IF NOT EXISTS streak ON TABLE knowledge_state TYPE int;
            DEFINE FIELD IF NOT EXISTS last_reviewed_at ON TABLE knowledge_state TYPE option<datetime>;
            DEFINE FIELD IF NOT EXISTS next_review_at ON TABLE knowledge_state TYPE option<datetime>;
            DEFINE FIELD IF NOT EXISTS updated_at ON TABLE knowledge_state TYPE datetime DEFAULT time::now();
            DEFINE INDEX IF NOT EXISTS ks_student_course ON TABLE knowledge_state FIELDS student_id, course_code, topic_id, bloom_level UNIQUE;

            DEFINE TABLE IF NOT EXISTS topic_prerequisite SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS course_code ON TABLE topic_prerequisite TYPE string;
            DEFINE FIELD IF NOT EXISTS topic_from ON TABLE topic_prerequisite TYPE string;
            DEFINE FIELD IF NOT EXISTS topic_to ON TABLE topic_prerequisite TYPE string;
            DEFINE FIELD IF NOT EXISTS prereq_type ON TABLE topic_prerequisite TYPE string;
            DEFINE INDEX IF NOT EXISTS tp_course_idx ON TABLE topic_prerequisite FIELDS course_code;

            DEFINE TABLE IF NOT EXISTS question_log SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS student_id ON TABLE question_log TYPE string;
            DEFINE FIELD IF NOT EXISTS course_code ON TABLE question_log TYPE string;
            DEFINE FIELD IF NOT EXISTS topic_id ON TABLE question_log TYPE string;
            DEFINE FIELD IF NOT EXISTS bloom_level ON TABLE question_log TYPE int;
            DEFINE FIELD IF NOT EXISTS question_text ON TABLE question_log TYPE option<string>;
            DEFINE FIELD IF NOT EXISTS is_correct ON TABLE question_log TYPE bool;
            DEFINE FIELD IF NOT EXISTS source ON TABLE question_log TYPE string;
            DEFINE FIELD IF NOT EXISTS timestamp ON TABLE question_log TYPE datetime DEFAULT time::now();
            DEFINE INDEX IF NOT EXISTS ql_student_course_idx ON TABLE question_log FIELDS student_id, course_code;
        """
        try:
            await db.query(schema_query)
            logger.info("Schema initialized (dimension=%d)", dim)
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
