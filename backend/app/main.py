from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

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
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.rag = RAGPipeline()
    app.state.engine = QueryEngine()
    app.state.curriculum = CurriculumManager()
    app.state.saved_content = SavedContentManager()
    print("Starting up RAG pipeline API...")
    yield
    print("Shutting down...")


app = FastAPI(title="Adaptive Learning RAG API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
