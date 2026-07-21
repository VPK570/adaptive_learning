"""Classifies student questions into Bloom's Taxonomy levels via LLM."""

import json

from app.openrouter import client

CLASSIFY_PROMPT = """Classify this student question into one Bloom's Taxonomy cognitive level.

1 = Remember: recall facts, definitions, lists
2 = Understand: explain, summarize, interpret
3 = Apply: use in new situation, solve problems
4 = Analyze: compare, contrast, find patterns, break down
5 = Evaluate: judge, critique, justify, defend
6 = Create: design, construct, invent, generate new ideas

Return ONLY a single integer (1-6).

Question: {text}"""

CLASSIFY_BATCH_PROMPT = """Classify each of the following student questions into one Bloom's Taxonomy cognitive level.

1 = Remember: recall facts, definitions, lists
2 = Understand: explain, summarize, interpret
3 = Apply: use in new situation, solve problems
4 = Analyze: compare, contrast, find patterns, break down
5 = Evaluate: judge, critique, justify, defend
6 = Create: design, construct, invent, generate new ideas

Return ONLY a JSON array of integers (1-6). One entry per question, in the same order.

Questions:
{text}"""

_bloom_cache: dict[str, int] = {}


async def classify_bloom_level(question: str) -> int | None:
    cached = _bloom_cache.get(question)
    if cached is not None:
        return cached
    try:
        response = await client.chat(
            [{"role": "user", "content": CLASSIFY_PROMPT.format(text=question)}],
            temperature=0.1,
            max_tokens=10,
        )
        cleaned = response.strip()
        level = int(cleaned)
        if 1 <= level <= 6:
            _bloom_cache[question] = level
            return level
    except (ValueError, TypeError):
        pass
    return None


async def classify_bloom_levels(questions: list[str]) -> list[int | None]:
    if not questions:
        return []

    unclassified = [q for q in questions if q not in _bloom_cache]
    results: dict[str, int] = {q: _bloom_cache[q] for q in questions if q in _bloom_cache}

    if unclassified:
        numbered = "\n".join(f"{i+1}. {q}" for i, q in enumerate(unclassified))
        try:
            response = await client.chat(
                [{"role": "user", "content": CLASSIFY_BATCH_PROMPT.format(text=numbered)}],
                temperature=0.1,
                max_tokens=100,
            )
            parsed = json.loads(response.strip())
            if isinstance(parsed, list):
                for q, level in zip(unclassified, parsed):
                    if isinstance(level, int) and 1 <= level <= 6:
                        _bloom_cache[q] = level
                        results[q] = level
        except (ValueError, TypeError, json.JSONDecodeError):
            pass

    return [results.get(q) for q in questions]
