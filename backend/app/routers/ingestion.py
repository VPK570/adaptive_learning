import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, Form, HTTPException
from typing import Annotated

from app.auth import require_role
from app.deps import get_rag, get_curriculum
from app.rag import RAGPipeline
from app.curriculum import CurriculumManager
from app.validation import (
    validate_course_code,
    sanitize_text,
    MAX_FILE_SIZE,
    MAX_COURSE_NAME_LENGTH,
    MAX_TOPIC_LENGTH,
)

router = APIRouter()


@router.post("/ingest")
async def ingest_pdf(
    file: Annotated[UploadFile, Form(description="PDF file to ingest")],
    course_code: Annotated[str, Form()] = "BAECE102",
    topic: Annotated[str, Form()] = "",
    rag: RAGPipeline = Depends(get_rag),
    _=Depends(require_role("faculty", "admin")),
):
    course_code = validate_course_code(course_code)
    topic = sanitize_text(topic, MAX_TOPIC_LENGTH)

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")

    temp_path = f"/tmp/ingest_{uuid.uuid4().hex}.pdf"
    try:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(413, "File size exceeds limit (15MB)")

        with open(temp_path, "wb") as f:
            f.write(content)

        title = Path(file.filename).stem.replace("-", " ").replace("_", " ")
        title = sanitize_text(title, MAX_COURSE_NAME_LENGTH)

        result = await rag.ingest_pdf(
            course_code=course_code,
            document_title=title,
            filepath=temp_path,
            topic=topic,
        )
        return result
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/curriculum")
async def upload_curriculum(
    file: Annotated[UploadFile, Form(...)],
    course_code: Annotated[str, Form(...)],
    curriculum: CurriculumManager = Depends(get_curriculum),
    _=Depends(require_role("faculty", "admin")),
):
    course_code = validate_course_code(course_code)
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")

    temp_path = f"/tmp/curriculum_{uuid.uuid4().hex}.pdf"
    try:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(413, "File size exceeds limit (15MB)")

        with open(temp_path, "wb") as f:
            f.write(content)

        title = Path(file.filename).stem.replace("-", " ").replace("_", " ")
        title = sanitize_text(title, MAX_COURSE_NAME_LENGTH)

        result = await curriculum.ingest_curriculum(
            course_code=course_code,
            document_title=title,
            filepath=temp_path,
        )
        return result
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
