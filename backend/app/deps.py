from fastapi import Request
from app.rag import RAGPipeline
from app.query_engine import QueryEngine
from app.curriculum import CurriculumManager
from app.knowledge_state import KnowledgeStateManager


def get_rag(request: Request) -> RAGPipeline:
    return request.app.state.rag


def get_engine(request: Request) -> QueryEngine:
    return request.app.state.engine


def get_curriculum(request: Request) -> CurriculumManager:
    return request.app.state.curriculum


def get_knowledge_state(request: Request) -> KnowledgeStateManager:
    return request.app.state.knowledge_state
