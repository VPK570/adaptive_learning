"""RAGAS-based evaluation of the RAG pipeline."""

import re
from typing import Any

from app.provider_router import router as client


class RG:
    """Faithfulness scorer using OpenRouter LLM."""

    async def faithfulness(self, response: str, contexts: list[str]) -> float:
        """
        Check how many claims in the response are supported by the contexts.
        Returns a score between 0 and 1.
        """
        if not response.strip():
            return 0.0

        contexts_text = "\n\n".join(
            f"Context {i+1}: {ctx}" for i, ctx in enumerate(contexts)
        )

        messages = [
            {
                "role": "system",
                "content": "You are an accuracy evaluator for educational AI responses.",
            },
            {
                "role": "user",
                "content": f"""Given a response and its source contexts, count how many factual claims
in the response are supported by the contexts. A claim is any statement that asserts a fact.

Response:
{response}

Contexts:
{contexts_text}

Rules:
- Ignore questions, greetings, and self-referential statements
- Each factual statement = one claim
- Count only claims that can be verified against the contexts
- If a claim contradicts the context, it does NOT count as supported

Output a single number: the fraction of claims that are supported (0.0 to 1.0).
Then on a new line, write: "X of Y claims supported" where X is supported count and Y is total count.

Example output:
0.85
7 of 8 claims supported""",
            },
        ]

        try:
            result = await client.chat(messages, temperature=0, max_tokens=256)
            lines = result.strip().split("\n")
            first_line = lines[0].strip()

            score = float(re.match(r"[\d.]+", first_line).group())
            return min(1.0, max(0.0, score))
        except Exception:
            return 0.0

    async def answer_relevancy(self, query: str, response: str) -> float:
        """Check how relevant the response is to the query."""
        messages = [
            {
                "role": "system",
                "content": "You evaluate answer relevance for educational AI.",
            },
            {
                "role": "user",
                "content": f"""Given a user query and the AI response, rate how well the response addresses the query.

Query: {query}

Response: {response}

Rate from 0.0 to 1.0:
- 1.0 = perfectly addresses the query
- 0.5 = partially addresses, misses some aspects
- 0.0 = doesn't address the query at all

Output a single number between 0.0 and 1.0, nothing else.""",
            },
        ]

        try:
            result = await client.chat(messages, temperature=0, max_tokens=64)
            return min(1.0, max(0.0, float(re.match(r"[\d.]+", result.strip()).group())))
        except Exception:
            return 0.0

    async def context_precision(self, query: str, retrieved_chunks: list[dict[str, Any]]) -> float:
        """Check what fraction of retrieved chunks are relevant to the query."""
        if not retrieved_chunks:
            return 0.0

        contexts_text = "\n\n".join(
            f"Chunk {i+1}: {c.get('text', c.get('chunk_text', ''))[:300]}"
            for i, c in enumerate(retrieved_chunks)
        )

        messages = [
            {
                "role": "system",
                "content": "You evaluate retrieval quality for educational AI.",
            },
            {
                "role": "user",
                "content": f"""Given a query and retrieved context chunks, count how many chunks
are actually relevant to answering the query.

Query: {query}

Retrieved Chunks:
{contexts_text}

A chunk is relevant if it contains information that helps answer the query.
Output a single number: fraction of chunks that are relevant (0.0 to 1.0).
Then on a new line: "X of Y chunks relevant".""",
            },
        ]

        try:
            result = await client.chat(messages, temperature=0, max_tokens=256)
            lines = result.strip().split("\n")
            score = float(re.match(r"[\d.]+", lines[0].strip()).group())
            return min(1.0, max(0.0, score))
        except Exception:
            return 0.0

    async def context_recall(self, query: str, response: str, retrieved_chunks: list[dict[str, Any]]) -> float:
        """Check what fraction of relevant information was retrieved."""
        if not retrieved_chunks:
            return 0.0

        contexts_text = "\n\n".join(
            f"Chunk {i+1}: {c.get('text', c.get('chunk_text', ''))[:300]}"
            for i, c in enumerate(retrieved_chunks)
        )

        prompt_text = (
            f"Given a query, a response, and retrieved chunks, estimate what fraction\n"
            f"of the information needed to answer the query was captured in the retrieved chunks.\n\n"
            f"Query: {query}\n\n"
            f"Response: {response}\n\n"
            f"Retrieved Chunks:\n"
            f"{contexts_text}\n\n"
            f'Output a single number (0.0 to 1.0): fraction of required information that was retrieved.\n'
            f'Then a new line: "Estimated recall: X%"'
        )

        messages = [
            {
                "role": "system",
                "content": "You evaluate context recall for educational AI.",
            },
            {
                "role": "user",
                "content": prompt_text,
            },
        ]

        try:
            result = await client.chat(messages, temperature=0, max_tokens=256)
            lines = result.strip().split("\n")
            score = float(re.match(r"[\d.]+", lines[0].strip()).group())
            return min(1.0, max(0.0, score))
        except Exception:
            return 0.0

    async def run_full_eval(
        self,
        query: str,
        response: str,
        retrieved_chunks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Run all RAGAS-style metrics."""
        contexts = [c.get("text", c.get("chunk_text", "")) for c in retrieved_chunks]

        faithfulness = await self.faithfulness(response, contexts)
        answer_relevancy = await self.answer_relevancy(query, response)
        context_precision = await self.context_precision(query, retrieved_chunks)
        context_recall = await self.context_recall(query, response, retrieved_chunks)

        return {
            "faithfulness": round(faithfulness, 3),
            "answer_relevancy": round(answer_relevancy, 3),
            "context_precision": round(context_precision, 3),
            "context_recall": round(context_recall, 3),
            "overall_score": round((faithfulness + answer_relevancy + context_precision + context_recall) / 4, 3),
        }


class RAGASEvaluator:
    """High-level evaluation interface."""

    def __init__(self):
        self.rg = RG()

    async def evaluate(
        self,
        query: str,
        response: str,
        retrieved_chunks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return await self.rg.run_full_eval(query, response, retrieved_chunks)

    async def evaluate_batch(
        self,
        test_cases: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Evaluate a batch of test cases.

        test_cases: [{query, expected_response, retrieved_chunks}, ...]
        """
        results = []
        for tc in test_cases:
            result = await self.evaluate(
                query=tc["query"],
                response=tc.get("response", ""),
                retrieved_chunks=tc.get("retrieved_chunks", []),
            )
            result["query"] = tc["query"]
            results.append(result)
        return results

    def print_report(self, results: list[dict[str, Any]]) -> str:
        if not results:
            return "No results to report."

        avg_faith = sum(r["faithfulness"] for r in results) / len(results)
        avg_ans_rel = sum(r["answer_relevancy"] for r in results) / len(results)
        avg_ctx_prec = sum(r["context_precision"] for r in results) / len(results)
        avg_ctx_rec = sum(r["context_recall"] for r in results) / len(results)
        avg_overall = sum(r["overall_score"] for r in results) / len(results)

        lines = [
            "=" * 60,
            "RAG PIPELINE EVALUATION REPORT",
            "=" * 60,
            f"Test cases evaluated: {len(results)}",
            "",
            "METRICS (target: >0.85 for faithfulness, >0.80 for others)",
            "-" * 40,
            f"  Faithfulness:      {avg_faith:.3f} {'✓' if avg_faith >= 0.85 else '✗'}",
            f"  Answer Relevancy:  {avg_ans_rel:.3f} {'✓' if avg_ans_rel >= 0.80 else '✗'}",
            f"  Context Precision: {avg_ctx_prec:.3f} {'✓' if avg_ctx_prec >= 0.80 else '✗'}",
            f"  Context Recall:     {avg_ctx_rec:.3f} {'✓' if avg_ctx_rec >= 0.80 else '✗'}",
            f"  Overall:            {avg_overall:.3f}",
            "",
        ]

        fails = [r for r in results if r["faithfulness"] < 0.85]
        if fails:
            lines.append(f"FAILED CASES ({len(fails)}):")
            for r in fails:
                lines.append(f"  - {r['query'][:80]}... (faith: {r['faithfulness']:.3f})")

        lines.append("=" * 60)
        return "\n".join(lines)