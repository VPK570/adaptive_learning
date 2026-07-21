#!/usr/bin/env python3
"""CLI script to evaluate the RAG pipeline end-to-end.

Usage:
    python scripts/eval_pipeline.py --pdf path/to/test.pdf --query "Your question?"
    python scripts/eval_pipeline.py --pdf path/to/test.pdf --query "Your question?" --no-eval

Requires SurrealDB running with test namespace configured via env vars.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


async def run_eval(pdf_path: str, course_code: str, query_text: str, skip_eval: bool = False):
    from app.rag import RAGPipeline
    from app.query_engine import QueryEngine
    from app.evaluator import RAGASEvaluator

    doc_title = Path(pdf_path).stem.replace("-", " ").replace("_", " ")

    print(f"Ingesting: {pdf_path}")
    rag = RAGPipeline()
    ingest_result = await rag.ingest_pdf(
        course_code=course_code,
        document_title=doc_title,
        filepath=pdf_path,
        topic="eval",
    )
    print(f"  Ingested {ingest_result.get('text_chunks', 0)} text chunks, "
          f"{ingest_result.get('image_chunks', 0)} image chunks")

    print(f"\nQuerying: {query_text}")
    engine = QueryEngine()
    query_result = await engine.query(
        query=query_text,
        course_code=course_code,
        course_name=course_code,
    )
    print(f"  Response preview: {query_result['response'][:200]}...")
    print(f"  Chunks retrieved: {query_result['chunks_retrieved']}")
    print(f"  Cited sources: {len(query_result['cited_sources'])}")

    if skip_eval:
        print("\nSkipping LLM-as-judge evaluation (--no-eval)")
        return

    retrieved = await rag.retrieve(query=query_text, course_code=course_code, top_k=5)

    print("\nRunning RAGAS-style evaluation (this calls OpenRouter)...")
    evaluator = RAGASEvaluator()
    test_case = {
        "query": query_text,
        "response": query_result["response"],
        "retrieved_chunks": retrieved,
    }
    results = await evaluator.evaluate_batch([test_case])
    report = evaluator.print_report(results)
    print(f"\n{report}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate RAG pipeline end-to-end")
    parser.add_argument("--pdf", required=True, help="Path to test PDF file")
    parser.add_argument("--course", default="BAECE102", help="Course code")
    parser.add_argument("--query", default="What is the main topic of this document?", help="Test query")
    parser.add_argument("--no-eval", action="store_true", help="Skip LLM-as-judge evaluation")
    args = parser.parse_args()

    if not os.path.exists(args.pdf):
        print(f"Error: PDF not found: {args.pdf}")
        sys.exit(1)

    asyncio.run(run_eval(
        pdf_path=args.pdf,
        course_code=args.course,
        query_text=args.query,
        skip_eval=args.no_eval,
    ))


if __name__ == "__main__":
    main()
