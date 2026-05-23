"""Extract text AND images from PDFs for multimodal RAG.

Pipeline:
1. Extract text per page (pypdf)
2. Extract images per page (pypdf /XObject)
3. Validate images via magic bytes (JPEG, PNG, GIF, BMP, WebP)
4. Skip invalid/garbage images (CCITT fax, JPEG2000, LZW, etc.)
5. Store images as base64 in ImageContent dataclass
6. Return: [(page_num, text, ImageContent list), ...]

Images are embedded natively using Nemotron VL — no captioning needed.
"""

import io
import base64
from dataclasses import dataclass
from typing import Generator

import pypdf

JPEG_MAGIC = b"\xFF\xD8\xFF"
PNG_MAGIC = b"\x89\x50\x4E\x47"
GIF_MAGIC = b"\x47\x49\x46\x38"
BMP_MAGIC = b"\x42\x4D"
RIFF_MAGIC = b"\x52\x49\x46\x46"
WEBP_MAGIC = b"\x57\x45\x42\x50"

MIME_TYPES = {
    b"\xFF\xD8\xFF": "image/jpeg",
    b"\x89\x50\x4E\x47": "image/png",
    b"\x47\x49\x46\x38": "image/gif",
    b"\x42\x4D": "image/bmp",
}


def detect_mime(data: bytes) -> str | None:
    if len(data) < 4:
        return None
    if data[:3] == JPEG_MAGIC:
        return "image/jpeg"
    if data[:4] == PNG_MAGIC:
        return "image/png"
    if data[:4] == GIF_MAGIC:
        return "image/gif"
    if data[:2] == BMP_MAGIC:
        return "image/bmp"
    if data[:4] == RIFF_MAGIC and data[8:12] == WEBP_MAGIC:
        return "image/webp"
    return None


@dataclass
class ImageContent:
    b64_str: str
    mime_type: str
    valid: bool
    bytes_size: int


@dataclass
class PageContent:
    page_num: int
    text: str
    images: list[ImageContent]


async def extract_all_pages(filepath: str) -> list[PageContent]:
    reader = pypdf.PdfReader(filepath)
    pages: list[PageContent] = []

    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        images: list[ImageContent] = []

        try:
            resources = page.get("/Resources", {})
            xobjects = resources.get("/XObject", {})

            if isinstance(xobjects, dict):
                for key, xobj_ref in xobjects.items():
                    xobj = xobj_ref.get_object()

                    if xobj.get("/Subtype") == "/Image":
                        try:
                            data = xobj.get_data()
                            if isinstance(data, bytes) and len(data) > 1000:
                                mime = detect_mime(data)
                                if mime:
                                    images.append(ImageContent(
                                        b64_str=base64.b64encode(data).decode("utf-8"),
                                        mime_type=mime,
                                        valid=True,
                                        bytes_size=len(data),
                                    ))
                        except Exception:
                            pass
        except Exception:
            pass

        pages.append(PageContent(page_num=i, text=text, images=images))

    return pages


async def extract_all_pages_from_bytes(pdf_bytes: bytes) -> list[PageContent]:
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    pages: list[PageContent] = []

    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        images: list[ImageContent] = []

        try:
            resources = page.get("/Resources", {})
            xobjects = resources.get("/XObject", {})

            if isinstance(xobjects, dict):
                for key, xobj_ref in xobjects.items():
                    xobj = xobj_ref.get_object()

                    if xobj.get("/Subtype") == "/Image":
                        try:
                            data = xobj.get_data()
                            if isinstance(data, bytes) and len(data) > 1000:
                                mime = detect_mime(data)
                                if mime:
                                    images.append(ImageContent(
                                        b64_str=base64.b64encode(data).decode("utf-8"),
                                        mime_type=mime,
                                        valid=True,
                                        bytes_size=len(data),
                                    ))
                        except Exception:
                            pass
        except Exception:
            pass

        pages.append(PageContent(page_num=i, text=text, images=images))

    return pages


def page_to_text_for_chunking(page: PageContent) -> str:
    parts = [f"[Page {page.page_num}]"]
    if page.text.strip():
        parts.append(page.text.strip())
    return "\n\n".join(parts)


def count_images_in_pdf(filepath: str) -> dict[str, int]:
    reader = pypdf.PdfReader(filepath)
    total_images = 0
    valid_images = 0
    pages_with_images = 0

    for i, page in enumerate(reader.pages, 1):
        has_image = False
        try:
            resources = page.get("/Resources", {})
            xobjects = resources.get("/XObject", {})

            if isinstance(xobjects, dict):
                for key, xobj_ref in xobjects.items():
                    xobj = xobj_ref.get_object()
                    if xobj.get("/Subtype") == "/Image":
                        try:
                            data = xobj.get_data()
                            if isinstance(data, bytes) and len(data) > 1000:
                                total_images += 1
                                if detect_mime(data):
                                    valid_images += 1
                                has_image = True
                        except Exception:
                            pass
        except Exception:
            pass

        if has_image:
            pages_with_images += 1

    return {
        "total_images": total_images,
        "valid_images": valid_images,
        "invalid_images": total_images - valid_images,
        "pages_with_images": pages_with_images,
        "total_pages": len(reader.pages),
    }