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
                print("=" * 50)
                print("CREATING NEW SURREALDB INSTANCE")
                print(f"URL: {settings.SURREAL_URL}")
                print(f"NS: {settings.SURREAL_NS}")
                print(f"DB: {settings.SURREAL_DB}")
                print("=" * 50)
                cls._instance = AsyncSurreal(settings.SURREAL_URL)
                await cls._instance.connect()
                print("Connected to SurrealDB")
                await cls._instance.signin({
                    "user": settings.SURREAL_USER,
                    "pass": settings.SURREAL_PASS,
                })
                print("Signed in to SurrealDB")
                await cls._instance.use(settings.SURREAL_NS, settings.SURREAL_DB)
                print(f"Using namespace {settings.SURREAL_NS} and database {settings.SURREAL_DB}")
                await cls._init_schema(cls._instance)
                print("Schema initialization completed")
                print("=" * 50)
            return cls._instance


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
            DEFINE FIELD IF NOT EXISTS created_at ON TABLE course TYPE string;
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
            
            DEFINE TABLE IF NOT EXISTS query_log SCHEMALESS;
            DEFINE FIELD IF NOT EXISTS course_code ON TABLE query_log TYPE string;
            DEFINE FIELD IF NOT EXISTS question ON TABLE query_log TYPE string;
            DEFINE FIELD IF NOT EXISTS response_preview ON TABLE query_log TYPE string;
            DEFINE FIELD IF NOT EXISTS timestamp ON TABLE query_log TYPE string;
            DEFINE FIELD IF NOT EXISTS out_of_scope ON TABLE query_log TYPE bool;
            DEFINE FIELD IF NOT EXISTS cited_sources ON TABLE query_log TYPE array;
        """
        try:
            print("Executing schema initialization...")
            await db.query(schema_query)
            print("Schema initialization completed successfully")
        except Exception as e:
            # Log the error and re-raise if it's not just about existing tables
            error_msg = str(e).lower()
            if "already exists" in error_msg or "duplicate" in error_msg:
                print(f"Schema initialization info (tables likely already exist): {e}")
            else:
                print(f"Schema initialization error: {e}")
                raise  # Re-raise the exception for critical errors

async def get_db():
    return await SurrealDBManager.get_db()

async def close_db():
    db = await SurrealDBManager.get_db()
    await db.close()
