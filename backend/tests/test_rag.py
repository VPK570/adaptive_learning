"""Tests for the RAG pipeline — chunking, citation, prompts, multimodal."""

import pytest

from app.chunker import chunk_text, clean_text
from app.citation import (
    has_citation, extract_all_citations, remove_uncited_claims,
    format_citation, validate_citations,
)
from app.query_engine import (
    build_tutor_system_prompt,
    build_context_window,
    build_tutor_prompt,
    QueryEngine,
)


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
    rag.delete_course("BAECE102")

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
    rag.delete_course("BAECE102")

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
    rag.delete_course("BAECE102")

    await rag.ingest(
        course_code="BAECE102",
        document_title="Test",
        text="Sequential circuits store state using flip-flops.",
        topic="test",
    )

    stats = rag.get_course_stats("BAECE102")
    assert stats["total_chunks"] >= 1
    assert stats["text_chunks"] >= 1
    assert "image_chunks" in stats


@pytest.mark.asyncio
async def test_count_and_list_courses():
    from app.rag import RAGPipeline

    rag = RAGPipeline()
    rag.delete_course("BAECE102_TEST")

    await rag.ingest("BAECE102_TEST", "Test", "Some content.", "test")

    count = rag.count_chunks("BAECE102_TEST")
    assert count >= 1

    courses = rag.list_courses()
    assert "BAECE102_TEST" in courses

    rag.delete_course("BAECE102_TEST")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
