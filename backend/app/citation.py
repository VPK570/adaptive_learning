"""Citation enforcement — every factual claim must cite a source chunk."""

import re

CITATION_RE = re.compile(r"\[Source:\s*[^\]]+\]", re.IGNORECASE)


def parse_citation(citation_text: str) -> tuple[str, str] | tuple[None, None]:
    """Extract title and page/slide number from a citation string."""
    # Matches: [Source: Title, Slide 5] or [Source: Title, Page 5]
    match = re.search(r"\[Source:\s*(.*?),\s*(?:Slide|Page|Unit)?\s*(\d+)\]", citation_text, re.IGNORECASE)
    if match:
        return match.group(1).strip().lower(), match.group(2).strip()
    
    # Fallback: [Source: Title, 5]
    match = re.search(r"\[Source:\s*(.*?),\s*(\d+)\]", citation_text, re.IGNORECASE)
    if match:
        return match.group(1).strip().lower(), match.group(2).strip()
        
    return None, None


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

    # Create a lookup set of (title, page) for fast matching
    valid_sources = set()
    for c in chunks:
        title = c.get("source_title", "").lower()
        page = str(c.get("page", ""))
        valid_sources.add((title, page))

    valid = 0
    detailed_results = []
    for cit in cited:
        title, page = parse_citation(cit)
        is_valid = False
        if title and page:
            # Direct match
            if (title, page) in valid_sources:
                is_valid = True
            else:
                # Loose title match if direct match fails
                for v_title, v_page in valid_sources:
                    if (v_title in title or title in v_title) and v_page == page:
                        is_valid = True
                        break
        
        if is_valid:
            valid += 1
        
        detailed_results.append({"citation": cit, "parsed": (title, page), "valid": is_valid})

    return {
        "valid": (valid / len(cited)) >= 0.8 if cited else False,
        "total_citations": len(cited),
        "valid_citations": valid,
        "coverage": round(valid / len(cited), 2) if cited else 0.0,
        "citations": cited,
        "details": detailed_results
    }