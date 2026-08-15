"""Tests for the RAG pipeline — chunking, citation, prompts, multimodal."""

import pytest
import pytest_asyncio

from app.chunker import chunk_text, clean_text
from app.citation import (
    extract_all_citations,
    format_citation,
    has_citation,
    validate_citations,
)
from app.query_engine import (
    build_context_window,
    build_tutor_prompt,
    build_tutor_system_prompt,
)


@pytest_asyncio.fixture(autouse=True)
async def reset_surreal_singleton():
    from app.db import SurrealDBManager
    SurrealDBManager._instance = None
    yield
    await SurrealDBManager.reset()


class TestChunking:
    def test_clean_text_removes_whitespace(self):
        dirty = "Hello    world\n\n\n\tworld"
        clean = clean_text(dirty)
        assert "\n" not in clean
        assert "\t" not in clean

    def test_clean_text_removes_page_numbers(self):
        text = "Chapter 1. Page 5 Page 42. End of chapter."
        cleaned = clean_text(text)
        assert "Page 5" not in cleaned

    def test_chunk_text_empty_returns_empty(self):
        assert chunk_text("", 50, 10) == []

    def test_chunk_text_small_returns_one(self):
        chunks = chunk_text("Short text.", 50, 10)
        assert len(chunks) == 1

    def test_chunk_text_produces_multiple(self):
        text = ". ".join([f"Sentence {i} with some content." for i in range(50)])
        chunks = chunk_text(text, chunk_size=50, overlap_tokens=10)
        assert len(chunks) >= 2
        assert all(isinstance(c, tuple) and len(c) == 3 for c in chunks)

    def test_ocr_fallback_adds_page_markers(self):
        import sys
        from types import SimpleNamespace
        from unittest.mock import patch

        from app import pdf_extractor as pe

        fake_convert = SimpleNamespace(convert_from_path=lambda path, dpi=300: [object()])
        fake_tess = SimpleNamespace(image_to_string=lambda img: "OCR line one\nOCR line two")
        with patch.dict(sys.modules, {"pdf2image": fake_convert, "pytesseract": fake_tess}):
            pages = pe._ocr_fallback("dummy.pdf")
        assert pages[0].text.startswith("[Page 1]")


class TestCitation:
    def test_has_citation_true(self):
        assert has_citation("Hash function [Source: Week 3, Slide 8] maps keys.")

    def test_has_citation_false(self):
        assert not has_citation("Some factual claim without source.")

    def test_extract_citations(self):
        text = "Hash [Source: Week 3, Slide 8]. Chaining [Source: Week 3, Slide 12]."
        cites = extract_all_citations(text)
        assert len(cites) == 2

    def test_format_citation(self):
        cit = format_citation("Data Structures Week 3", 8)
        assert "Data Structures Week 3" in cit
        assert "8" in cit

    def test_validate_citations_valid(self):
        text = "Hash functions [Source: Data Structures Week 3, Slide 8] work."
        chunks = [{"source_title": "Data Structures Week 3", "page": 8}]
        result = validate_citations(text, chunks)
        assert result["valid"] is True
        assert result["coverage"] >= 0.8

    def test_validate_citations_hallucinated_slide(self):
        text = "Water boils at 100 degrees [Source: Chemistry, Slide 99]."
        chunks = [{"source_title": "Chemistry", "page": 5}]
        result = validate_citations(text, chunks)
        assert result["valid"] is False

    def test_validate_citations_no_citations(self):
        result = validate_citations("Some claim", [])
        assert result["valid"] is False
        assert result["reason"] == "No citations found"


class TestQueryEngine:
    def test_system_prompt_includes_course(self):
        prompt = build_tutor_system_prompt("Data Structures", "CS201", "English", 0.65)
        assert "CS201" in prompt
        assert "Data Structures" in prompt

    def test_system_prompt_high_mastery(self):
        prompt = build_tutor_system_prompt("Algorithms", "CS301", "English", 0.85)
        assert "strong mastery" in prompt.lower() or "synthesis" in prompt.lower()

    def test_system_prompt_low_mastery(self):
        prompt = build_tutor_system_prompt("Algorithms", "CS301", "English", 0.2)
        assert "low mastery" in prompt.lower() or "struggling" in prompt.lower()

    def test_context_window_text_chunks(self):
        chunks = [
            {"source_title": "Lecture 1", "page": 5, "content_type": "text", "text": "Hash functions map keys."},
            {"source_title": "Lecture 2", "page": 8, "content_type": "text", "text": "Collision resolution."},
        ]
        context = build_context_window(chunks, [])
        assert "COURSE MATERIALS" in context
        assert "Lecture 1" in context
        assert "Lecture 2" in context

    def test_context_window_image_chunks(self):
        chunks = [
            {"source_title": "Lecture 1", "page": 5, "content_type": "image", "has_image": True,
             "text": "Circuit diagram showing a D flip-flop with clock input..."},
        ]
        context = build_context_window(chunks, [])
        assert "RELEVANT IMAGES" in context
        assert "Circuit diagram" in context

    def test_context_window_mixed_chunks(self):
        chunks = [
            {"source_title": "Lecture 1", "page": 5, "content_type": "text", "text": "Hash functions map keys."},
            {"source_title": "Lecture 1", "page": 5, "content_type": "image", "has_image": True,
             "text": "Diagram: Hash table with chaining."},
        ]
        context = build_context_window(chunks, [])
        assert "Text 1" in context
        assert "Image 1" in context

    def test_context_window_truncates_history(self):
        chunks = [{"source_title": "Test", "content_type": "text", "text": "content"}]
        history = [{"role": "user", "content": f"Q{i}"} for i in range(15)]
        context = build_context_window(chunks, history, max_turns=5)
        assert "earlier turns summarized" in context
        assert "Q14" in context
        assert "Q0" not in context

    def test_build_tutor_prompt_returns_list(self):
        chunks = [{"source_title": "Test", "page": 1, "content_type": "text", "text": "content"}]
        messages = build_tutor_prompt(
            query="What is hashing?",
            course_code="CS201",
            course_name="Data Structures",
            chunks=chunks,
            history=[],
        )
        assert isinstance(messages, list)
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "STUDENT: What is hashing?" in messages[1]["content"]


@pytest.mark.asyncio
async def test_ingest_text_chunks():
    from app.rag import RAGPipeline

    rag = RAGPipeline()
    await rag.delete_course("BAECE102")

    result = await rag.ingest(
        course_code="BAECE102",
        document_title="Sequential Circuits",
        text="Sequential circuits store state. They use flip-flops. "
             "Synchronous circuits use a clock. Asynchronous circuits do not.",
        topic="sequential-circuits",
    )

    assert result["chunks_ingested"] > 0
    assert result["course_code"] == "BAECE102"


@pytest.mark.asyncio
async def test_retrieve_returns_chunks():
    from app.rag import RAGPipeline

    rag = RAGPipeline()
    await rag.delete_course("BAECE102")

    await rag.ingest(
        course_code="BAECE102",
        document_title="Sequential Circuits",
        text="A flip-flop stores one bit of state.",
        topic="flip-flops",
    )

    chunks = await rag.retrieve(query="flip-flop", course_code="BAECE102", top_k=5)
    assert len(chunks) >= 1


@pytest.mark.asyncio
async def test_stats_includes_content_types():
    from app.rag import RAGPipeline

    rag = RAGPipeline()
    await rag.delete_course("BAECE102")

    await rag.ingest(
        course_code="BAECE102",
        document_title="Test",
        text="Sequential circuits store state using flip-flops.",
        topic="test",
    )

    stats = await rag.get_course_stats("BAECE102")
    assert stats["total_chunks"] >= 1
    assert stats["text_chunks"] >= 1
    assert "image_chunks" in stats


@pytest.mark.asyncio
async def test_count_and_list_courses():
    from app.rag import RAGPipeline

    rag = RAGPipeline()
    await rag.delete_course("BAECE102_TEST")

    await rag.ingest("BAECE102_TEST", "Test", "Some content.", "test")

    count = await rag.count_chunks("BAECE102_TEST")
    assert count >= 1

    courses = await rag.list_courses()
    assert "BAECE102_TEST" in courses

    await rag.delete_course("BAECE102_TEST")


class TestChunkerEdgeCases:
    def test_extract_page_for_chunk_no_marker(self):
        from app.chunker import extract_page_for_chunk
        assert extract_page_for_chunk("Some text", "Some full text", 0) == 1

    def test_extract_page_for_chunk_with_markers(self):
        from app.chunker import extract_page_for_chunk
        full_text = "[Page 1] Intro [Page 2] Middle [Page 3] End"
        # chunk starting at "Middle" should get page 2
        idx = full_text.index("Middle")
        assert extract_page_for_chunk("Middle", full_text, idx) == 2

    def test_extract_page_for_chunk_marker_inside(self):
        from app.chunker import extract_page_for_chunk
        full_text = "[Page 1] Some text [Page 2] More text"
        idx = full_text.index("More text")
        assert extract_page_for_chunk("More text", full_text, idx) == 2

    def test_token_count_empty(self):
        from app.chunker import token_count
        assert token_count("") == 0

    def test_token_count_nonempty(self):
        from app.chunker import token_count
        assert token_count("hello world") > 0

    def test_clean_text_preserves_page_markers(self):
        from app.chunker import clean_text
        result = clean_text("Some text [Page 5] more text")
        assert "[Page 5]" in result

    def test_clean_text_removes_fake_page_numbers(self):
        from app.chunker import clean_text
        result = clean_text("Chapter 1. Page 42 Page 43. End.")
        assert "Page 42" not in result

    def test_clean_text_disallowed_chars(self):
        from app.chunker import clean_text
        result = clean_text("hello\x00world\x7ftest")
        assert "\x00" not in result
        assert "\x7f" not in result

    def test_chunk_text_no_sentences(self):
        from app.chunker import chunk_text
        assert chunk_text("", 50, 10) == []
        assert chunk_text("   ", 50, 10) == []


from app.citation import parse_citation
from app.citation import remove_uncited_claims as _remove_uncited_claims


class TestCitationEdgeCases:

    def test_parse_citation_standard(self):
        title, page = parse_citation("[Source: Data Structures, Slide 8]")
        assert title == "data structures"
        assert page == "8"

    def test_parse_citation_page_variant(self):
        title, page = parse_citation("[Source: DLD Notes, Page 42]")
        assert title == "dld notes"
        assert page == "42"

    def test_parse_citation_unit_variant(self):
        title, page = parse_citation("[Source: Chemistry, Unit 3]")
        assert title == "chemistry"
        assert page == "3"

    def test_parse_citation_fallback_no_label(self):
        title, page = parse_citation("[Source: Notes, 7]")
        assert title == "notes"
        assert page == "7"

    def test_parse_citation_no_match_returns_none(self):
        assert parse_citation("No citation here") == (None, None)

    def test_parse_citation_empty(self):
        assert parse_citation("") == (None, None)

    def test_format_citation_default(self):
        result = format_citation("DLD Notes", 5)
        assert "DLD Notes" in result
        assert "5" in result
        assert "Slide" in result

    def test_format_citation_custom_type(self):
        result = format_citation("DLD Notes", 5, cite_type="page")
        assert "Page" in result

    def test_remove_uncited_claims_basic(self):
        text = "The moon is made entirely of cheese according to reports. [Source: Notes, Slide 1]"
        result = _remove_uncited_claims(text)
        assert "cheese" not in result
        assert "Source: Notes" in result

    def test_remove_uncited_claims_keeps_questions(self):
        text = "What do you think? The moon is made of cheese."
        result = _remove_uncited_claims(text)
        assert "What do you think?" in result

    def test_remove_uncited_claims_keeps_cited_sentences(self):
        text = "Hash function maps keys [Source: DLD, Slide 8]. Random claim has no evidence whatsoever according to experts."
        result = _remove_uncited_claims(text)
        assert "Hash function" in result
        assert "Random claim" not in result


# ── PDF helpers (inlined from test_e2e_pipeline) ──

def _make_test_pdf(text: str) -> bytes:
    encoded = text.encode("latin-1", errors="replace")
    content = b"BT /F1 12 Tf 100 700 Td (" + encoded + b") Tj ET"
    stream = b"stream\n" + content + b"\nendstream"
    stream_len = str(len(content)).encode()

    obj1 = b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    obj2 = b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    obj3 = b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
    obj4 = b"4 0 obj<</Length " + stream_len + b">>" + stream + b"endobj\n"
    obj5 = b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"

    body = obj1 + obj2 + obj3 + obj4 + obj5
    offsets = [0]
    pos = 9
    for obj in [obj1, obj2, obj3, obj4, obj5]:
        offsets.append(pos)
        pos += len(obj)

    xref_entries = b"".join(f"{o:010d} 00000 n \n".encode() for o in offsets)
    trailer = (
        b"xref\n0 6\n" + xref_entries +
        b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n" +
        str(pos).encode() + b"\n%%EOF"
    )
    return b"%PDF-1.4\n" + body + trailer


TEST_PDF_TEXT = (
    "This document covers data structures. Arrays store elements "
    "contiguously in memory. Linked lists use pointers between nodes."
)


@pytest.mark.asyncio
async def test_topic_analysis_stored_on_ingest_pdf():
    import os
    import tempfile

    from app.db import get_db
    from app.rag import RAGPipeline

    rag = RAGPipeline()
    db = await get_db()
    course = "TEST_TA"

    # idempotent: clear leftovers from a prior interrupted run
    await db.query("DELETE course_topic WHERE course_code = $code", {"code": course})
    await db.query("DELETE document WHERE course_code = $code", {"code": course})

    # seed a course topic so coverage computation has data
    await db.query(
        "INSERT INTO course_topic $t",
        {"t": {
            "course_code": course, "topic_name": "arrays",
            "subtopics": [], "prerequisites": [],
            "learning_objectives": [], "order_index": 1,
        }},
    )

    pdf_bytes = _make_test_pdf(TEST_PDF_TEXT)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(pdf_bytes)
        path = f.name

    try:
        result = await rag.ingest_pdf(
            course_code=course,
            document_title="Data Structures Notes",
            filepath=path,
            topic="data-structures",
        )
        assert "doc_id" in result
        assert result["course_code"] == course

        docs = await db.query(
            "SELECT topic_analysis FROM document WHERE course_code = $code",
            {"code": course},
        )
        assert docs, "document record should exist"
        ta = docs[0].get("topic_analysis")
        assert isinstance(ta, dict), "topic_analysis should be a dict"
        assert "topics" in ta
        assert "module_coverage" in ta
        assert "extra_topics" in ta
        assert "total_chunks" in ta
        assert "uncategorized_chunks" in ta
        # the seeded topic "arrays" should appear in coverage
        topic_names = [t["topic_name"] for t in ta["topics"]]
        assert "arrays" in topic_names
    finally:
        await db.query("DELETE document WHERE course_code = $code", {"code": course})
        await db.query("DELETE course_topic WHERE course_code = $code", {"code": course})
        await rag.delete_course(course)
        if os.path.exists(path):
            os.remove(path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
