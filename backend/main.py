import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

"""CLI script — ingest PDFs (text + images), query, evaluate.

No Docker needed — ChromaDB for vector storage, OpenRouter for LLM + Embeddings.
Images are embedded natively via Nemotron VL — no captioning needed.
"""

import argparse
import asyncio
import os

from dotenv import load_dotenv
load_dotenv()


def parse_args():
    p = argparse.ArgumentParser(description="RAG Pipeline — ingest PDFs (with images), query, evaluate")
    sub = p.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="Ingest a single document")
    ingest.add_argument("--course", "-c", required=True, help="Course code, e.g. BAECE102")
    ingest.add_argument("--title", "-t", required=True, help="Document title")
    ingest.add_argument("--file", "-f", required=True, help="Path to .txt or .pdf")
    ingest.add_argument("--topic", default="", help="Topic tag")

    ingest_batch = sub.add_parser("ingest-batch", help="Ingest multiple files")
    ingest_batch.add_argument("--course", "-c", required=True, help="Course code")
    ingest_batch.add_argument("--dir", "-d", required=True, help="Directory")
    ingest_batch.add_argument("--glob", default="*.pdf", help="Glob pattern")

    query = sub.add_parser("query", help="Query the RAG system")
    query.add_argument("--course", "-c", required=True, help="Course code")
    query.add_argument("--question", "-q", required=True, help="Question")
    query.add_argument("--language", default="English")
    query.add_argument("--top-k", "-k", type=int, default=5)
    query.add_argument(
        "--type",
        choices=["all", "text", "image"],
        default="all",
        help="Retrieve text chunks, image chunks, or both",
    )

    eval_cmd = sub.add_parser("eval", help="Run evaluation")
    eval_cmd.add_argument("--course", "-c", required=True)
    eval_cmd.add_argument("--cases", "-n", type=int, default=10)
    eval_cmd.add_argument("--report", action="store_true")

    stats = sub.add_parser("stats", help="Show course stats")
    stats.add_argument("--course", "-c", required=True)

    return p.parse_args()


def extract_pdf_text(filepath: str) -> str:
    import pypdf

    reader = pypdf.PdfReader(filepath)
    parts: list[str] = []

    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text()
        if text:
            parts.append(f"[Page {i}]\n{text}")

    return "\n\n".join(parts)


def extract_text(filepath: str) -> str:
    ext = filepath.lower().split(".")[-1]

    if ext == "pdf":
        return extract_pdf_text(filepath)
    elif ext in ("txt", "md", "text"):
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file type: .{ext}")


def basename_to_title(filepath: str) -> str:
    name = os.path.basename(filepath)
    name = os.path.splitext(name)[0]
    name = name.replace("-", " ").replace("_", " ").replace("  ", " ")
    return name.strip()


async def run_ingest(course: str, title: str, filepath: str, topic: str):
    from app.db import reset as _reset_db
    from app.rag import RAGPipeline

    await _reset_db()
    rag = RAGPipeline()

    print(f"Extracting content from: {filepath}")
    print(f"Course: {course} | Title: {title} | Topic: {topic}")

    ext = filepath.lower().split(".")[-1]
    if ext == "pdf":
        result = await rag.ingest_pdf(
            course_code=course,
            document_title=title,
            filepath=filepath,
            topic=topic,
        )
    else:
        text = extract_text(filepath)
        if not text.strip():
            print(f"Error: no text extracted from '{filepath}'")
            return
        print(f"Characters: {len(text):,}")
        result = await rag.ingest(
            course_code=course,
            document_title=title,
            text=text,
            topic=topic,
        )

    print(f"\n✓ Ingested {result.get('text_chunks', 0) + result.get('image_chunks', 0)} chunks")
    if "text_chunks" in result:
        print(f"  Text chunks: {result.get('text_chunks', 0)}")
        print(f"  Image chunks: {result.get('image_chunks', 0)}")

    await print_stats(course)


async def run_ingest_batch(course: str, directory: str, glob_pattern: str):
    import glob
    from app.db import reset as _reset_db
    from app.rag import RAGPipeline

    await _reset_db()
    rag = RAGPipeline()

    pattern = os.path.join(directory, glob_pattern)
    files = sorted(glob.glob(pattern))

    if not files:
        print(f"No files found: {pattern}")
        return

    print(f"Found {len(files)} files\n")

    total_text = 0
    total_images = 0

    for i, filepath in enumerate(files, 1):
        title = basename_to_title(filepath)

        print(f"[{i}/{len(files)}] {os.path.basename(filepath)}")
        print(f"  Title: {title}")

        try:
            ext = filepath.lower().split(".")[-1]

            if ext == "pdf":
                result = await rag.ingest_pdf(
                    course_code=course,
                    document_title=title,
                    filepath=filepath,
                    topic="",
                )
            else:
                text = extract_text(filepath)
                if not text.strip():
                    print(f"  ⚠ No text extracted, skipping")
                    continue
                result = await rag.ingest(
                    course_code=course,
                    document_title=title,
                    text=text,
                    topic="",
                )

            total_text += result.get("text_chunks", 0)
            total_images += result.get("image_chunks", 0)

            img_str = ""
            if result.get("image_chunks", 0) > 0:
                img_str = f" + {result['image_chunks']} image chunks"

            print(f"  ✓ {result.get('text_chunks', 0) + result.get('image_chunks', 0)} chunks ingested{img_str}")

        except Exception as e:
            print(f"  ✗ Error: {e}")

        await asyncio.sleep(0.3)

    print(f"\n{'='*60}")
    print(f"Batch complete:")
    print(f"  Text chunks: {total_text}")
    print(f"  Image chunks: {total_images}")
    await print_stats(course)


async def run_query(
    course: str,
    question: str,
    language: str,
    top_k: int,
    content_type: str,
):
    from app.rag import RAGPipeline
    from app.query_engine import QueryEngine

    rag = RAGPipeline()
    engine = QueryEngine()

    chunks_type = None if content_type == "all" else content_type

    chunks = await rag.retrieve(
        query=question,
        course_code=course,
        top_k=top_k,
        content_type=chunks_type,
    )

    if not chunks:
        print(f"No chunks found for course '{course}'. Ingest documents first.")
        return

    text_chunks = [c for c in chunks if c.get("content_type", "text") != "image"]
    image_chunks = [c for c in chunks if c.get("content_type") == "image" or c.get("has_image")]

    print(f"Retrieved {len(chunks)} chunks "
          f"({len(text_chunks)} text, {len(image_chunks)} image)\n")

    for i, c in enumerate(text_chunks, 1):
        score = 1 - c.get("distance", 0)
        print(f"  [T{i}] {c['source_title']} (Slide {c['page']}, score: {score:.3f})")
        print(f"       {c['text'][:200]}...")
        print()

    for i, c in enumerate(image_chunks, 1):
        score = 1 - c.get("distance", 0)
        print(f"  [IMG{i}] {c['source_title']} (Slide {c['page']}, score: {score:.3f})")
        print(f"       {c['text'][:200]}")
        print()

    result = await engine.query(
        query=question,
        course_code=course,
        course_name=course,
        chunks=chunks,
        language=language,
    )

    print("=" * 60)
    print("RESPONSE:")
    print("=" * 60)
    print(result["response"])
    print()

    text_sources = [s for s in result["cited_sources"] if s["content_type"] != "image"]
    image_sources = [s for s in result["cited_sources"] if s["content_type"] == "image" or s["has_image"]]

    if text_sources:
        print("Text sources:")
        for src in text_sources:
            print(f"  - {src['source_title']} (Slide {src['page']})")

    if image_sources:
        print("Image sources referenced:")
        for src in image_sources:
            print(f"  - {src['source_title']} (Slide {src['page']})")

    cc = result["citation_check"]
    print(f"\nCitation check: {'✓ VALID' if cc['valid'] else '✗ INVALID'} "
          f"({cc.get('coverage', 0)*100:.0f}% coverage)")


async def run_evaluation(course: str, cases: int, report: bool):
    from app.rag import RAGPipeline
    from app.query_engine import QueryEngine
    from app.evaluator import RAGASEvaluator

    rag = RAGPipeline()
    engine = QueryEngine()
    evaluator = RAGASEvaluator()

    questions = [
        "What is a sequential circuit?",
        "Explain the difference between synchronous and asynchronous counters",
        "What is a finite state machine?",
        "Explain Mealy vs Moore state machine",
        "What are the steps to design a synchronous counter?",
        "What is the excitation table of a flip-flop?",
        "Explain state minimization in FSM",
        "What are PLDs and when are they used?",
        "What is the difference between combinational and sequential circuits?",
        "How do you convert a state diagram to a state table?",
    ]

    test_questions = questions[:cases]
    print(f"Evaluating {len(test_questions)} test cases...\n")

    results = []
    for i, q in enumerate(test_questions, 1):
        chunks = await rag.retrieve(query=q, course_code=course, top_k=5)

        if not chunks:
            print(f"  [{i}/{len(test_questions)}] {q[:50]}... — SKIP (no chunks)")
            continue

        result = await engine.query(query=q, course_code=course, course_name=course, chunks=chunks)

        eval_result = await evaluator.evaluate(
            query=q,
            response=result["response"],
            retrieved_chunks=chunks,
        )

        img_note = ""
        if result.get("image_chunks", 0) > 0:
            img_note = f" [IMG:{result['image_chunks']}]"

        print(f"  [{i}/{len(test_questions)}] {q[:50]}...{img_note}")
        print(f"       Faith: {eval_result['faithfulness']:.3f} | "
              f"Relevancy: {eval_result['answer_relevancy']:.3f} | "
              f"Overall: {eval_result['overall_score']:.3f}")

        eval_result["query"] = q
        results.append(eval_result)

    print()
    print(evaluator.print_report(results))


async def print_stats(course: str):
    from app.rag import RAGPipeline
    rag = RAGPipeline()
    stats = await rag.get_course_stats(course)
    print(f"  Stats: {stats['total_chunks']} total chunks "
          f"({stats['text_chunks']} text, {stats['image_chunks']} image)")


async def run_stats(course: str):
    rag = RAGPipeline()
    stats = await rag.get_course_stats(course)
    print(f"Course: {stats['course_code']}")
    print(f"Total chunks: {stats['total_chunks']}")
    print(f"  Text chunks: {stats['text_chunks']}")
    print(f"  Image chunks: {stats['image_chunks']}")
    print(f"Topics:")
    for t in stats["topics"]:
        print(f"  - {t['topic']}: {t['chunks']} chunks")


async def main():
    args = parse_args()

    if args.command == "ingest":
        await run_ingest(args.course, args.title, args.file, args.topic)
    elif args.command == "ingest-batch":
        await run_ingest_batch(args.course, args.dir, args.glob)
    elif args.command == "query":
        await run_query(args.course, args.question, args.language, args.top_k, args.type)
    elif args.command == "eval":
        await run_evaluation(args.course, args.cases, args.report)
    elif args.command == "stats":
        await run_stats(args.course)


if __name__ == "__main__":
    asyncio.run(main())