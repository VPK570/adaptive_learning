import logging
import sys
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

from app.config import settings
from app.database import Database
from app.rag import RAGPipeline
from app.query_engine import QueryEngine
from app.curriculum import CurriculumManager
from app.saved_content import SavedContentManager
from app.validation import MAX_FILE_SIZE
from app.auth import decode_token
from app.routers import admin as admin_routes, ingestion, query, courses, analytics, chat, flashcards, quiz, paper, auth as auth_routes
from app.routers import users as users_routes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def seed_default_users():
    from app.auth import hash_password
    from app.stores.user_store import UserStore
    defaults = [
        ("student@test.com", "password123", "student"),
        ("faculty@test.com", "password123", "faculty"),
        ("admin@test.com", "password123", "admin"),
    ]
    async with Database.session() as session:
        store = UserStore(session)
        for email, pw, role in defaults:
            existing = await store.get_by_email(email)
            if existing:
                logger.info("Default user already exists: %s", email)
            else:
                await store.create(email, hash_password(pw), role)
                logger.info("Created default user: %s (%s)", email, role)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Database.init()
    await Database.wait_ready()
    await Database.create_all()
    await seed_default_users()
    app.state.rag = RAGPipeline()
    app.state.engine = QueryEngine()
    app.state.curriculum = CurriculumManager()
    app.state.saved_content = SavedContentManager()
    logger.info("Starting up RAG pipeline API...")
    yield
    logger.info("Shutting down...")
    await Database.close()


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


@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    if request.method in ["POST", "PUT"]:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_FILE_SIZE:
            return Response(content="File size exceeds limit", status_code=413)
    return await call_next(request)


PUBLIC_PREFIXES = ("/auth", "/health", "/docs", "/openapi.json", "/redoc")


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path
    if path.startswith(PUBLIC_PREFIXES):
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
app.include_router(analytics.router)
app.include_router(chat.router)
app.include_router(ingestion.router)
app.include_router(flashcards.router)
app.include_router(quiz.router)
app.include_router(paper.router)
app.include_router(auth_routes.router)
app.include_router(users_routes.router)
app.include_router(admin_routes.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
