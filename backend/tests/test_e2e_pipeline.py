"""End-to-end integration test for the full RAG pipeline.

Tests: ingest PDF → retrieve → generate response → validate citations.
"""

import os
import tempfile
import pytest
from app.rag import RAGPipeline
from app.query_engine import QueryEngine
from app.citation import validate_citations, remove_uncited_claims

_e2e = pytest.mark.skipif(True, reason="E2E integration tests — requires running infra + OpenRouter API key")


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
        b"xref\n"
        b"0 6\n"
        + xref_entries
        + b"trailer<</Size 6/Root 1 0 R>>\n"
        + b"startxref\n"
        + str(pos).encode() + b"\n"
        + b"%%EOF"
    )

    return b"%PDF-1.4\n" + body + trailer


TEST_PDF_TEXT = (
    "The French Revolution began in 1789 and ended in 1799. "
    "It was a period of radical social and political upheaval in France. "
    "Key events include the Storming of the Bastille on July 14, 1789, "
    "and the Reign of Terror from 1793 to 1794. "
    "The revolution abolished the monarchy and established a republic."
)


@pytest.fixture
def test_pdf_path():
    pdf_bytes = _make_test_pdf(TEST_PDF_TEXT)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(pdf_bytes)
        path = f.name
    yield path
    if os.path.exists(path):
        os.remove(path)


@_e2e
@pytest.mark.asyncio
async def test_ingest_pdf(test_pdf_path):
    rag = RAGPipeline()
    result = await rag.ingest_pdf(
        course_code="TEST101",
        document_title="French Revolution Notes",
        filepath=test_pdf_path,
        topic="history",
    )
    assert result["text_chunks"] > 0, "Should ingest at least one text chunk"
    assert result["course_code"] == "TEST101"
    return result


@_e2e
@pytest.mark.asyncio
async def test_query_after_ingest(test_pdf_path):
    rag = RAGPipeline()
    await rag.ingest_pdf(
        course_code="TEST101",
        document_title="French Revolution Notes",
        filepath=test_pdf_path,
        topic="history",
    )

    engine = QueryEngine()
    result = await engine.query(
        query="When did the French Revolution begin?",
        course_code="TEST101",
        course_name="Test Course",
    )
    assert "response" in result
    assert "1789" in result["response"], "Response should mention 1789"
    assert result["chunks_retrieved"] > 0, "Should retrieve chunks"


@_e2e
@pytest.mark.asyncio
async def test_citation_validation(test_pdf_path):
    rag = RAGPipeline()
    await rag.ingest_pdf(
        course_code="TEST101",
        document_title="French Revolution Notes",
        filepath=test_pdf_path,
        topic="history",
    )

    engine = QueryEngine()
    result = await engine.query(
        query="What happened during the French Revolution?",
        course_code="TEST101",
        course_name="Test Course",
    )
    response = result["response"]

    chunks = await engine.rag_pipeline.retrieve(
        query="French Revolution",
        course_code="TEST101",
        top_k=5,
    )
    if chunks:
        citation_result = validate_citations(response, chunks)
        assert "total_citations" in citation_result


@_e2e
@pytest.mark.asyncio
async def test_remove_uncited_claims():
    text = "The French Revolution started in 1789. [Source: Notes, Slide 1] "
    text += "The moon is made of cheese. "
    text += "What do you think?"
    cleaned = remove_uncited_claims(text)
    assert "1789" in cleaned
    assert "cheese" not in cleaned
