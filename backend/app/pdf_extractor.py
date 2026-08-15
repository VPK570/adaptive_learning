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

import asyncio
import base64
import io
import logging
from dataclasses import dataclass

import pypdf

logger = logging.getLogger(__name__)

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


def _extract_page_images(page) -> list[ImageContent]:
    """Extract valid images from a single PDF page."""
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
                    except Exception as e:
                        logger.warning(f"Failed to extract image {key} on page {page.page_number}: {e}")
    except Exception as e:
        logger.warning(f"Failed to process resources on page {page.page_number}: {e}")
    return images


def _sync_extract_all_pages(source: str | bytes) -> list[PageContent]:
    reader = pypdf.PdfReader(io.BytesIO(source) if isinstance(source, bytes) else source)
    pages: list[PageContent] = []

    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        text = f"[Page {i}]\n" + text
        images = _extract_page_images(page)
        pages.append(PageContent(page_num=i, text=text, images=images))

    return pages


@dataclass
class Section:
    heading: str
    page_start: int
    page_end: int
    text: str


import re

# ponytail: simple heading regex — fails on unusual PDF layouts.
# Upgrade to layout-aware detection (pdfminer) if too many false splits.
SECTION_HEADING_RE = re.compile(
    r"^(?:"
    r"(?:[A-Z][A-Z\s]{2,50})|"
    r"(?:(?:Chapter|Module|Unit|Lesson|Section|Part|Topic)\s+\d+[\s:.].*)|"
    r"(?:\d+\.\d+(?:\.\d+)?\s+[A-Z].*)|"
    r"(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})"
    r")\s*$"
)


def detect_sections(pages: list[PageContent]) -> list[Section]:
    """Split extracted pages into sections using heading heuristics."""
    lines_with_pages = []
    for page in pages:
        for line in page.text.split("\n"):
            lines_with_pages.append((line.strip(), page.page_num))

    sections: list[Section] = []
    current_heading = "Introduction"
    current_page_start = lines_with_pages[0][1] if lines_with_pages else 1
    current_lines: list[str] = []

    for line, page_num in lines_with_pages:
        if not line:
            current_lines.append("")
            continue
        if SECTION_HEADING_RE.match(line):
            if current_lines:
                sections.append(Section(
                    heading=current_heading,
                    page_start=current_page_start,
                    page_end=page_num,
                    text="\n".join(current_lines).strip(),
                ))
            current_heading = line
            current_page_start = page_num
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append(Section(
            heading=current_heading,
            page_start=current_page_start,
            page_end=lines_with_pages[-1][1],
            text="\n".join(current_lines).strip(),
        ))

    return sections


def _ocr_fallback(pdf_path: str) -> list[PageContent]:
    """Fallback OCR for scanned/image PDFs. Uses pdf2image + pytesseract."""
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except ImportError:
        logger.warning("OCR dependencies not installed — add pytesseract and pdf2image to requirements.txt")
        return []

    try:
        images = convert_from_path(pdf_path, dpi=300)
    except Exception as e:
        logger.error("pdf2image failed: %s", e)
        return []

    pages = []
    for i, img in enumerate(images, 1):
        try:
            text = pytesseract.image_to_string(img)
        except Exception as e:
            logger.warning("OCR failed on page %d: %s", i, e)
            text = ""
        pages.append(PageContent(page_num=i, text=f"[Page {i}]\n{text}", images=[]))

    return pages


async def extract_all_pages(source: str | bytes) -> list[PageContent]:
    pages = await asyncio.to_thread(_sync_extract_all_pages, source)

    # Check if OCR fallback needed (< 30% pages have meaningful text)
    non_empty = [p for p in pages if len(p.text.strip()) > 50]
    if len(non_empty) < max(1, len(pages) * 0.3):
        pdf_path = source if isinstance(source, str) else ""
        if pdf_path:
            logger.info("Low text yield from pypdf (%d/%d pages) — trying OCR", len(non_empty), len(pages))
            ocr_pages = _ocr_fallback(pdf_path)
            if ocr_pages and len(ocr_pages) == len(pages):
                for i, (orig, ocr) in enumerate(zip(pages, ocr_pages)):
                    if len(orig.text.strip()) < 50 and ocr.text.strip():
                        pages[i] = ocr
                logger.info("OCR recovered text for %d pages",
                            sum(1 for p in pages if len(p.text.strip()) > 50))

    return pages
