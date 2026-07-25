import logging
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

from app.logging_middleware import request_id_var  # noqa: E402

# Ensure every log record has request_id before any module logs
_old_factory = logging.getLogRecordFactory()
def _make_record(*args, **kwargs):
    r = _old_factory(*args, **kwargs)
    r.request_id = request_id_var.get()[:8] or "-"
    return r
logging.setLogRecordFactory(_make_record)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(request_id)s | %(name)s | %(message)s",
    force=True,
)

from app.config import settings  # noqa: E402
from app.rag import RAGPipeline  # noqa: E402
from app.query_engine import QueryEngine  # noqa: E402
from app.curriculum import CurriculumManager  # noqa: E402
from app.knowledge_state import KnowledgeStateManager  # noqa: E402
from app.validation import MAX_FILE_SIZE  # noqa: E402
from app.auth import decode_token  # noqa: E402
from app.routers import ingestion, query, courses, chat, flashcards, quiz, paper, analytics, images, auth as auth_routes  # noqa: E402
from app.routers import admin as admin_routes, users as users_routes, learning_path as learning_path_routes, tasks as tasks_routes  # noqa: E402

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.auth import hash_password, _create_user, get_user_by_email
    from app.db import SurrealDBManager
    await SurrealDBManager.get_db()

    defaults = [
        ("student@test.com", "password123", "student"),
        ("faculty@test.com", "password123", "faculty"),
        ("admin@test.com", "password123", "admin"),
    ]
    for email, pw, role in defaults:
        existing = await get_user_by_email(email)
        if not existing:
            await _create_user(email, hash_password(pw), role)
            logger.info("Created default user: %s (%s)", email, role)

    app.state.rag = RAGPipeline()
    app.state.engine = QueryEngine()
    app.state.curriculum = CurriculumManager()
    app.state.knowledge_state = KnowledgeStateManager()
    logger.info("Starting up RAG pipeline API...")
    yield
    logger.info("Shutting down...")


app = FastAPI(title="Adaptive Learning RAG API", version="1.0.0", lifespan=lifespan)

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


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    if request.method in ["POST", "PUT"]:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_FILE_SIZE:
            return Response(content="File size exceeds limit", status_code=413)
    return await call_next(request)


PUBLIC_PREFIXES = ("/auth", "/health", "/docs", "/openapi.json", "/redoc")


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    rid = request.headers.get("X-Request-ID", uuid.uuid4().hex[:12])
    request.state.request_id = rid
    token = request_id_var.set(rid)
    try:
        return await call_next(request)
    finally:
        request_id_var.reset(token)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path
    if path.startswith(PUBLIC_PREFIXES) or request.method == "OPTIONS" or \
       (request.method == "GET" and path.startswith("/chat-images/")):
        return await call_next(request)

    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})

    try:
        payload = decode_token(auth[len("Bearer "):])
        request.state.user = {"email": payload.get("sub"), "role": payload.get("role", "student")}
    except Exception:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})

    return await call_next(request)


app.include_router(query.router)
app.include_router(courses.router)
app.include_router(chat.router)
app.include_router(ingestion.router)
app.include_router(flashcards.router)
app.include_router(quiz.router)
app.include_router(paper.router)
app.include_router(images.router)
app.include_router(auth_routes.router)
app.include_router(analytics.router)
app.include_router(users_routes.router)
app.include_router(admin_routes.router)
app.include_router(learning_path_routes.router, prefix="/api")
app.include_router(tasks_routes.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
