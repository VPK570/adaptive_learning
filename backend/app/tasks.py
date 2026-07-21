import asyncio
import os
import logging
from celery import Celery, signals

from app.logging_middleware import request_id_var

logger = logging.getLogger(__name__)

celery_app = Celery("adaptive_learner")

_worker_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_worker_loop)
celery_app.config_from_object({
    "broker_url": os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0"),
    "result_backend": os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
    "task_serializer": "json",
    "result_serializer": "json",
    "accept_content": ["json"],
    "result_expires": 3600,
    "task_track_started": True,
    "task_acks_late": True,
    "worker_prefetch_multiplier": 1,
})


@signals.before_task_publish.connect
def propagate_request_id(headers, **kwargs):
    rid = request_id_var.get()
    if rid:
        headers["request_id"] = rid


@signals.task_prerun.connect
def restore_request_id(task, **kwargs):
    headers = getattr(task.request, "headers", {}) or {}
    rid = headers.get("request_id", "")
    if rid:
        request_id_var.set(rid)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5, autoretry_for=(ValueError,))
def ingest_pdf_task(self, course_code: str, document_title: str, filepath: str, topic: str = "", metadata: dict | None = None) -> dict:
    from app.rag import RAGPipeline
    rag = RAGPipeline()
    try:
        return _worker_loop.run_until_complete(rag.ingest_pdf(
            course_code=course_code,
            document_title=document_title,
            filepath=filepath,
            topic=topic,
            metadata=metadata,
        ))
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5, autoretry_for=(ValueError,))
def ingest_curriculum_task(self, course_code: str, document_title: str, filepath: str, topic: str = "") -> dict:
    from app.curriculum import CurriculumManager
    cm = CurriculumManager()
    try:
        return _worker_loop.run_until_complete(cm.ingest_curriculum(
            course_code=course_code,
            document_title=document_title,
            filepath=filepath,
            topic=topic,
        ))
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
