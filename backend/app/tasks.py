import asyncio
import logging
import os

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


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def ingest_pdf_task(self, course_code: str, document_title: str, filepath: str, topic: str = "", metadata: dict | None = None) -> dict:
    import shutil
    from pathlib import Path

    # Move file to permanent storage
    pdfs_dir = Path("storage") / "pdfs" / course_code
    pdfs_dir.mkdir(parents=True, exist_ok=True)

    import hashlib
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(4096), b""):
            sha256.update(block)
    content_hash = sha256.hexdigest()
    doc_id = content_hash[:16]
    permanent_path = pdfs_dir / f"{doc_id}.pdf"
    file_url = f"/pdfs/{course_code}/{doc_id}.pdf"
    file_size = os.path.getsize(filepath)

    if os.path.exists(str(permanent_path)):
        os.remove(filepath)
    else:
        shutil.move(filepath, str(permanent_path))

    from app.rag import RAGPipeline
    rag = RAGPipeline()
    try:
        result = _worker_loop.run_until_complete(rag.ingest_pdf(
            course_code=course_code,
            document_title=document_title,
            filepath=str(permanent_path),
            topic=topic,
            metadata=metadata,
            file_size=file_size,
            file_url=file_url,
        ))
        result["doc_id"] = doc_id
        return result
    finally:
        if os.path.exists(str(permanent_path)) and os.path.getsize(str(permanent_path)) == 0:
            os.remove(str(permanent_path))


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
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


