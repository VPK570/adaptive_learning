"""RAGAS-based evaluation of the RAG pipeline."""

import re
from typing import Any

from app.provider_router import router as client


def _parse_score(text: str) -> float:
    try:
        m = re.match(r"[\d.]+", text.strip())
        return min(1.0, max(0.0, float(m.group()))) if m else 0.0
    except Exception:
        return 0.0


class RAGASEvaluator:
    async def faithfulness(self, response: str, contexts: list[str]) -> float:
        if not response.strip():
            return 0.0
        contexts_text = "\n\n".join(f"Context {i+1}: {ctx}" for i, ctx in enumerate(contexts))
        messages = [
            {"role": "system", "content": "You are an accuracy evaluator for educational AI responses."},
            {"role": "user", "content": (
                "Given a response and its source contexts, count how many factual claims "
                "in the response are supported by the contexts.\n\n"
                f"Response:\n{response}\n\nContexts:\n{contexts_text}\n\n"
                "Rules:\n- Ignore questions, greetings, and self-referential statements\n"
                "- Each factual statement = one claim\n"
                "- Count only claims that can be verified against the contexts\n"
                "- If a claim contradicts the context, it does NOT count as supported\n\n"
                "Output a single number: the fraction of claims that are supported (0.0 to 1.0).\n"
                'Then on a new line, write: "X of Y claims supported".'
            )},
        ]
        try:
            result = await client.chat(messages, temperature=0, max_tokens=256)
            return _parse_score(result.strip().split("\n")[0])
        except Exception:
            return 0.0

    async def answer_relevancy(self, query: str, response: str) -> float:
        messages = [
            {"role": "system", "content": "You evaluate answer relevance for educational AI."},
            {"role": "user", "content": (
                "Given a user query and the AI response, rate how well the response addresses the query.\n\n"
                f"Query: {query}\n\nResponse: {response}\n\n"
                "Rate from 0.0 to 1.0:\n- 1.0 = perfectly addresses the query\n"
                "- 0.5 = partially addresses, misses some aspects\n"
                "- 0.0 = doesn't address the query at all\n\n"
                "Output a single number between 0.0 and 1.0, nothing else."
            )},
        ]
        try:
            result = await client.chat(messages, temperature=0, max_tokens=64)
            return _parse_score(result)
        except Exception:
            return 0.0

    async def context_precision(self, query: str, retrieved_chunks: list[dict[str, Any]]) -> float:
        if not retrieved_chunks:
            return 0.0
        contexts_text = "\n\n".join(
            f"Chunk {i+1}: {c.get('text', c.get('chunk_text', ''))[:300]}" for i, c in enumerate(retrieved_chunks)
        )
        messages = [
            {"role": "system", "content": "You evaluate retrieval quality for educational AI."},
            {"role": "user", "content": (
                "Given a query and retrieved context chunks, count how many chunks "
                "are actually relevant to answering the query.\n\n"
                f"Query: {query}\n\nRetrieved Chunks:\n{contexts_text}\n\n"
                "A chunk is relevant if it contains information that helps answer the query.\n"
                "Output a single number: fraction of chunks that are relevant (0.0 to 1.0).\n"
                'Then on a new line: "X of Y chunks relevant".'
            )},
        ]
        try:
            result = await client.chat(messages, temperature=0, max_tokens=256)
            return _parse_score(result.strip().split("\n")[0])
        except Exception:
            return 0.0

    async def context_recall(self, query: str, response: str, retrieved_chunks: list[dict[str, Any]]) -> float:
        if not retrieved_chunks:
            return 0.0
        contexts_text = "\n\n".join(
            f"Chunk {i+1}: {c.get('text', c.get('chunk_text', ''))[:300]}" for i, c in enumerate(retrieved_chunks)
        )
        messages = [
            {"role": "system", "content": "You evaluate context recall for educational AI."},
            {"role": "user", "content": (
                "Given a query, a response, and retrieved chunks, estimate what fraction "
                "of the information needed to answer the query was captured in the retrieved chunks.\n\n"
                f"Query: {query}\n\nResponse: {response}\n\nRetrieved Chunks:\n{contexts_text}\n\n"
                "Output a single number (0.0 to 1.0): fraction of required information that was retrieved.\n"
                'Then a new line: "Estimated recall: X%".'
            )},
        ]
        try:
            result = await client.chat(messages, temperature=0, max_tokens=256)
            return _parse_score(result.strip().split("\n")[0])
        except Exception:
            return 0.0

    async def evaluate(self, query: str, response: str, retrieved_chunks: list[dict[str, Any]]) -> dict[str, Any]:
        contexts = [c.get("text", c.get("chunk_text", "")) for c in retrieved_chunks]
        faith = await self.faithfulness(response, contexts)
        rel = await self.answer_relevancy(query, response)
        prec = await self.context_precision(query, retrieved_chunks)
        rec = await self.context_recall(query, response, retrieved_chunks)
        return {
            "faithfulness": round(faith, 3),
            "answer_relevancy": round(rel, 3),
            "context_precision": round(prec, 3),
            "context_recall": round(rec, 3),
            "overall_score": round((faith + rel + prec + rec) / 4, 3),
        }

    async def evaluate_batch(self, test_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results = []
        for tc in test_cases:
            r = await self.evaluate(tc["query"], tc.get("response", ""), tc.get("retrieved_chunks", []))
            r["query"] = tc["query"]
            results.append(r)
        return results

    def print_report(self, results: list[dict[str, Any]]) -> str:
        if not results:
            return "No results to report."
        n = len(results)
        def avg(k):
            return sum(r[k] for r in results) / n
        lines = [
            "=" * 60, "RAG PIPELINE EVALUATION REPORT", "=" * 60,
            f"Test cases evaluated: {n}", "",
            "METRICS (target: >0.85 for faithfulness, >0.80 for others)", "-" * 40,
            f"  Faithfulness:      {avg('faithfulness'):.3f} {'✓' if avg('faithfulness') >= 0.85 else '✗'}",
            f"  Answer Relevancy:  {avg('answer_relevancy'):.3f} {'✓' if avg('answer_relevancy') >= 0.80 else '✗'}",
            f"  Context Precision: {avg('context_precision'):.3f} {'✓' if avg('context_precision') >= 0.80 else '✗'}",
            f"  Context Recall:     {avg('context_recall'):.3f} {'✓' if avg('context_recall') >= 0.80 else '✗'}",
            f"  Overall:            {avg('overall_score'):.3f}", "",
        ]
        fails = [r for r in results if r["faithfulness"] < 0.85]
        if fails:
            lines.append(f"FAILED CASES ({len(fails)}):")
            for r in fails:
                lines.append(f"  - {r['query'][:80]}... (faith: {r['faithfulness']:.3f})")
        lines.append("=" * 60)
        return "\n".join(lines)
