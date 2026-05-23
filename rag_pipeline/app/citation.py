"""Citation enforcement — every factual claim must cite a source chunk."""

import re

CITATION_RE = re.compile(r"\[Source:\s*[^\]]+\]", re.IGNORECASE)


def has_citation(text: str) -> bool:
    return bool(CITATION_RE.search(text))


def extract_all_citations(text: str) -> list[str]:
    if not isinstance(text, str):
        return []
    return CITATION_RE.findall(text)


def remove_uncited_claims(text: str) -> str:
    """Remove or flag claims that lack a citation."""
    sentences = text.split(". ")
    kept = []
    dropped = 0

    for s in sentences:
        if CITATION_RE.search(s) or "?" in s or len(s) < 30 or s.strip().startswith("Can you") or s.strip().startswith("What"):
            kept.append(s)
        else:
            dropped += 1

    if dropped:
        result = ". ".join(kept)
        result += f"\n[Note: {dropped} claim(s) above could not be verified against course materials.]"
        return result
    return ". ".join(kept)


def format_citation(title: str, page: int | str, cite_type: str = "slide") -> str:
    return f"[Source: {title}, {cite_type.title()} {page}]"


def validate_citations(response: str, chunks: list[dict]) -> dict:
    cited = extract_all_citations(response)
    if not cited:
        return {"valid": False, "reason": "No citations found", "coverage": 0.0}

    titles = {c.get("source_title", "").lower() for c in chunks}
    valid = 0
    for cit in cited:
        cit_lower = cit.lower()
        if any(t in cit_lower or any(w in cit_lower for w in t.split() if len(w) > 4) for t in titles):
            valid += 1

    return {
        "valid": (valid / len(cited)) >= 0.8,
        "total_citations": len(cited),
        "valid_citations": valid,
        "coverage": round(valid / len(cited), 2),
        "citations": cited,
    }