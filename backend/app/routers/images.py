import base64
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Form, UploadFile, File, HTTPException, Response
from fastapi.responses import FileResponse

from app.validation import MAX_IMAGE_SIZE, sanitize_id

TRANSPARENT_PIXEL = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)

logger = logging.getLogger(__name__)

router = APIRouter()

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads" / "chat"

JPEG_HEADER = b"\xff\xd8\xff"
PNG_HEADER = b"\x89PNG"


def _validate_image_magic(head: bytes) -> str:
    if head[:3] == JPEG_HEADER:
        return "image/jpeg"
    if head[:4] == PNG_HEADER:
        return "image/png"
    raise HTTPException(status_code=400, detail="Only JPEG and PNG images are supported")


@router.post("/chat-images")
async def upload_image(file: UploadFile = File(...), session_id: str = Form("default")):
    safe_session = sanitize_id(session_id)
    head = await file.read(4)
    mime = _validate_image_magic(head)
    session_dir = UPLOAD_DIR / safe_session
    session_dir.mkdir(parents=True, exist_ok=True)
    ext = ".jpg" if mime == "image/jpeg" else ".png"
    image_id = f"{safe_session}/{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / image_id
    total = len(head)
    with open(dest, "wb") as f:
        f.write(head)
        while chunk := await file.read(8192):
            total += len(chunk)
            if total > MAX_IMAGE_SIZE:
                dest.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="File exceeds 5MB limit")
            f.write(chunk)
    logger.info("Uploaded image %s (%d bytes, %s)", image_id, total, mime)
    return {"image_id": image_id}


@router.get("/chat-images/{session_id}/{file_name}")
async def get_image(session_id: str, file_name: str):
    safe_session = sanitize_id(session_id)
    requested = (UPLOAD_DIR / safe_session / file_name).resolve()
    base = UPLOAD_DIR.resolve()
    if not str(requested).startswith(str(base)):
        return Response(content=TRANSPARENT_PIXEL, media_type="image/png", status_code=200)
    if not requested.is_file():
        return Response(content=TRANSPARENT_PIXEL, media_type="image/png", status_code=200)
    return FileResponse(str(requested))
