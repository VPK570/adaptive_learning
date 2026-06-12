from fastapi import Request
from app.rag import RAGPipeline
from app.query_engine import QueryEngine
from app.curriculum import CurriculumManager
from app.saved_content import SavedContentManager


def get_rag(request: Request) -> RAGPipeline:
    return request.app.state.rag


def get_engine(request: Request) -> QueryEngine:
    return request.app.state.engine


def get_curriculum(request: Request) -> CurriculumManager:
    return request.app.state.curriculum


def get_saved_content(request: Request) -> SavedContentManager:
    return request.app.state.saved_content
