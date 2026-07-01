import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.database import Database
from app.rag import RAGPipeline
from app.query_engine import QueryEngine
from app.curriculum import CurriculumManager
from app.saved_content import SavedContentManager
from app.validation import MAX_FILE_SIZE
from app.routers import (
    ingestion,
    query,
    courses,
    analytics,
    chat,
    flashcards,
    quiz,
    paper,
    auth as auth_routes,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Database.init()
    if not await Database.wait_ready():
        logger.warning("Postgres not available at startup — some endpoints will fail until DB is reachable")
    await Database.create_all()
    logger.info("Postgres connected and tables created")

    app.state.rag = RAGPipeline()
    app.state.engine = QueryEngine()
    app.state.curriculum = CurriculumManager()
    app.state.saved_content = SavedContentManager()
    logger.info("Starting up RAG pipeline API...")
    yield
    logger.info("Shutting down...")
    await Database.close()


app = FastAPI(title="Adaptive Learning RAG API", version="1.0.0", lifespan=lifespan)

# --- Rate limiting (slowapi) ---
# Keyed by client IP. 60 requests/minute per IP across all routes by default.
# NOTE: in-memory storage counts per server process. For multiple backend
# instances, switch to Redis via Limiter(..., storage_uri="redis://...").
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    if request.method in ["POST", "PUT"]:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_FILE_SIZE:
            return Response(content="File size exceeds limit", status_code=413)
    return await call_next(request)


app.include_router(query.router)
app.include_router(courses.router)
app.include_router(analytics.router)
app.include_router(chat.router)
app.include_router(ingestion.router)
app.include_router(flashcards.router)
app.include_router(quiz.router)
app.include_router(paper.router)
app.include_router(auth_routes.router)
