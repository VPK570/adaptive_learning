import os
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Query, UploadFile

from app.auth import require_role
from app.db import get_db
from app.tasks import ingest_curriculum_task, ingest_pdf_task
from app.validation import (
    MAX_COURSE_NAME_LENGTH,
    MAX_FILE_SIZE,
    MAX_TOPIC_LENGTH,
    sanitize_text,
    validate_course_code,
)

router = APIRouter()


@router.post("/ingest")
async def ingest_pdf(
    file: Annotated[UploadFile, Form(description="PDF file to ingest")],
    course_code: Annotated[str, Form()] = "BAECE102",
    topic: Annotated[str, Form()] = "",
    _=Depends(require_role("faculty", "admin")),
):
    course_code = validate_course_code(course_code)
    topic = sanitize_text(topic, MAX_TOPIC_LENGTH)

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "File size exceeds limit (15MB)")

    temp_path = f"/app/storage/ingest_{uuid.uuid4().hex}.pdf"
    try:
        with open(temp_path, "wb") as f:
            f.write(content)

        title = Path(file.filename).stem.replace("-", " ").replace("_", " ")
        title = sanitize_text(title, MAX_COURSE_NAME_LENGTH)

        task = ingest_pdf_task.delay(
            course_code=course_code,
            document_title=title,
            filepath=temp_path,
            topic=topic,
        )
        return {"task_id": task.id, "status": "PENDING"}
    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise


@router.post("/curriculum")
async def upload_curriculum(
    file: Annotated[UploadFile, Form(...)],
    course_code: Annotated[str, Form(...)],
    topic: Annotated[str, Form()] = "",
    _=Depends(require_role("faculty", "admin")),
):
    course_code = validate_course_code(course_code)
    topic = sanitize_text(topic, MAX_TOPIC_LENGTH)
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "File size exceeds limit (15MB)")

    temp_path = f"/app/storage/curriculum_{uuid.uuid4().hex}.pdf"
    try:
        with open(temp_path, "wb") as f:
            f.write(content)

        title = Path(file.filename).stem.replace("-", " ").replace("_", " ")
        title = sanitize_text(title, MAX_COURSE_NAME_LENGTH)

        task = ingest_curriculum_task.delay(
            course_code=course_code,
            document_title=title,
            filepath=temp_path,
            topic=topic,
        )
        return {"task_id": task.id, "status": "PENDING"}
    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise


@router.delete("/materials/{course_code}")
async def delete_material(
    course_code: str,
    filename: str = Query(...),
    _=Depends(require_role("faculty", "admin")),
):
    import os
    # Get file_path from document record for physical file cleanup
    db = await get_db()
    doc = await db.query(
        "SELECT file_path FROM document WHERE course_code = $code AND filename = $title",
        {"code": course_code, "title": filename},
    )
    file_path = doc[0].get("file_path") if doc else None

    await db.query("DELETE text_chunk WHERE course_code = $code AND source_title = $title",
                   {"code": course_code, "title": filename})
    await db.query("DELETE image_chunk WHERE course_code = $code AND source_title = $title",
                   {"code": course_code, "title": filename})
    await db.query("DELETE document WHERE course_code = $code AND filename = $title",
                   {"code": course_code, "title": filename})

    # Delete physical file if exists
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass  # Log or ignore file deletion errors
    return {"status": "success"}


@router.delete("/curriculum/{course_code}")
async def delete_curriculum(
    course_code: str,
    filename: str = Query(...),
    _=Depends(require_role("faculty", "admin")),
):
    import os
    course_code = validate_course_code(course_code)
    db = await get_db()

    # Get file_path from document record for physical file cleanup
    doc = await db.query(
        "SELECT file_path FROM document WHERE course_code = $code AND filename = $title",
        {"code": course_code, "title": filename},
    )
    file_path = doc[0].get("file_path") if doc else None

    await db.query("DELETE curriculum_chunk WHERE course_code = $code AND source_title = $title",
                   {"code": course_code, "title": filename})
    await db.query("DELETE document WHERE course_code = $code AND filename = $title",
                   {"code": course_code, "title": filename})
    # ponytail: clear topics instead of re-extracting
    await db.query("DELETE course_topic WHERE course_code = $code", {"code": course_code})
    await db.query("DELETE topic_prerequisite WHERE course_code = $code", {"code": course_code})

    # Delete physical file if exists
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass  # Log or ignore file deletion errors
    return {"status": "success"}
