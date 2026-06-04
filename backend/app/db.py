"""SurrealDB client — unified storage for vectors and documents."""

import asyncio
from typing import Optional
from surrealdb import AsyncSurreal
from app.config import settings

class SurrealDBManager:
    _instance: Optional[AsyncSurreal] = None
    _lock = asyncio.Lock()

    @classmethod
    async def get_db(cls) -> AsyncSurreal:
        async with cls._lock:
            if cls._instance is None:
                cls._instance = AsyncSurreal(settings.SURREAL_URL)
                await cls._instance.connect()
                await cls._instance.signin({
                    "user": settings.SURREAL_USER,
                    "pass": settings.SURREAL_PASS,
                })
                await cls._instance.use(settings.SURREAL_NS, settings.SURREAL_DB)
                await cls._init_schema(cls._instance)
            return cls._instance

    @classmethod
    async def _init_schema(cls, db: AsyncSurreal):
        """Initialize SurrealDB schema."""
        # Simple schema for testing/base
        await db.query("""
            DEFINE TABLE text_chunk SCHEMAFULL;
            DEFINE FIELD course_code ON TABLE text_chunk TYPE string;
            DEFINE FIELD text ON TABLE text_chunk TYPE string;
            DEFINE FIELD embedding ON TABLE text_chunk TYPE array<float>;
            DEFINE FIELD source_title ON TABLE text_chunk TYPE string;
            DEFINE FIELD topic ON TABLE text_chunk TYPE string;
            DEFINE FIELD page ON TABLE text_chunk TYPE number;
            DEFINE FIELD content_type ON TABLE text_chunk TYPE string;
            
            -- Full-Text Search Index
            DEFINE ANALYZER chunk_analyzer TOKENIZERS blank,punct FILTERS lowercase,snowball(english);
            DEFINE INDEX text_search_idx ON TABLE text_chunk FIELDS text FULLTEXT ANALYZER chunk_analyzer BM25;

            DEFINE TABLE image_chunk SCHEMAFULL;
            DEFINE FIELD course_code ON TABLE image_chunk TYPE string;
            DEFINE FIELD text ON TABLE image_chunk TYPE string;
            DEFINE FIELD embedding ON TABLE image_chunk TYPE array<float>;
            DEFINE FIELD source_title ON TABLE image_chunk TYPE string;
            DEFINE FIELD topic ON TABLE image_chunk TYPE string;
            DEFINE FIELD page ON TABLE image_chunk TYPE number;
            DEFINE FIELD content_type ON TABLE image_chunk TYPE string;
            DEFINE FIELD mime_type ON TABLE image_chunk TYPE string;
            DEFINE FIELD image_size_kb ON TABLE image_chunk TYPE number;
            
            DEFINE TABLE curriculum_chunk SCHEMAFULL;
            DEFINE FIELD course_code ON TABLE curriculum_chunk TYPE string;
            
            DEFINE TABLE course SCHEMAFULL;
            DEFINE FIELD course_code ON TABLE course TYPE string;
            DEFINE INDEX course_code_idx ON TABLE course FIELDS course_code UNIQUE;
            
            DEFINE TABLE chat_history SCHEMAFULL;
            DEFINE FIELD course_code ON TABLE chat_history TYPE string;
            DEFINE FIELD session_id ON TABLE chat_history TYPE string;
            DEFINE FIELD role ON TABLE chat_history TYPE string;
            DEFINE FIELD content ON TABLE chat_history TYPE string;
            DEFINE FIELD timestamp ON TABLE chat_history TYPE string;
            
            DEFINE TABLE flashcard_set SCHEMAFULL;
            DEFINE FIELD course_code ON TABLE flashcard_set TYPE string;
            
            DEFINE TABLE quiz SCHEMAFULL;
            DEFINE FIELD course_code ON TABLE quiz TYPE string;
            
            DEFINE TABLE query_log SCHEMAFULL;
            DEFINE FIELD course_code ON TABLE query_log TYPE string;
        """)

async def get_db():
    return await SurrealDBManager.get_db()

async def close_db():
    db = await SurrealDBManager.get_db()
    await db.close()
