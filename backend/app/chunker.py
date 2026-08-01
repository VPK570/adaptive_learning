"""Text chunking utilities — 512-token sentence-aware chunking."""

from dataclasses import dataclass, field
import re
import tiktoken



_encoder = None

def _get_encoder():
    global _encoder
    if _encoder is None:
        _encoder = tiktoken.get_encoding("cl100k_base")
    return _encoder


def token_count(text: str) -> int:
    return len(_get_encoder().encode(text))

def chunk_text(
    text: str,
    chunk_size: int = 512,
    overlap_tokens: int = 64,
) -> list[tuple[str, int, int]]:
    """
    Split text into overlapping chunks of ~chunk_size tokens.
    Respects sentence boundaries.

    Returns: list of (chunk_text, start_char, end_char)
    """
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[tuple[str, int, int]] = []

    if not text.strip() or not sentences or all(not s.strip() for s in sentences):
        return []
    current_sentences: list[str] = []
    current_token_count: int = 0
    start_char: int = 0

    for sentence in sentences:
        sentence_tokens = token_count(sentence)
        total_after = current_token_count + sentence_tokens + len(current_sentences)

        if total_after > chunk_size and current_sentences:
            chunk_text_str = " ".join(current_sentences)
            chunks.append((chunk_text_str, start_char, start_char + len(chunk_text_str)))

            overlap_count = min(len(current_sentences), 3)
            if overlap_count > 0:
                overlap_sents = current_sentences[-overlap_count:]
                current_sentences = overlap_sents
                current_token_count = sum(token_count(s)  for s in overlap_sents)
                start_char = start_char + len(" ".join(current_sentences[:len(current_sentences) - overlap_count])) + 1
                start_char = max(start_char, chunks[-1][2] - 200)
            else:
                current_sentences = []
                current_token_count = 0

        current_sentences.append(sentence)
        current_token_count += sentence_tokens

    if current_sentences:
        chunks.append((" ".join(current_sentences), start_char, start_char + len(" ".join(current_sentences))))

    return chunks


def clean_text(text: str) -> str:
    # Preserve [Page X] markers by temporarily replacing them
    text = re.sub(r"\[Page (\d+)\]", r"__PAGE_\1__", text)

    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", text)
    text = re.sub(r"\bPage\s+\d+\b", "", text)
    text = re.sub(r"-\n", "", text)

    # Restore [Page X] markers
    text = re.sub(r"__PAGE_(\d+)__", r"[Page \1]", text)
    return text.strip()


@dataclass
class Chunk:
    text: str
    page: int
    topic: str
    section_heading: str
    start_char: int = 0
    end_char: int = 0


def chunk_by_topic_regions(
    regions: list[dict],
    chunk_size: int = 512,
    overlap_tokens: int = 64,
) -> list[Chunk]:
    """Late chunking: run chunk_text on each topic region. All child chunks inherit topic + heading."""
    chunks: list[Chunk] = []
    for region in regions:
        if not region["text"].strip():
            continue
        raw_chunks = chunk_text(region["text"], chunk_size, overlap_tokens)
        for chunk_text_str, start, end in raw_chunks:
            page = extract_page_for_chunk(chunk_text_str, region["text"], start)
            chunks.append(Chunk(
                text=chunk_text_str, page=page,
                topic=region["topic"], section_heading=region["heading"],
                start_char=start, end_char=end,
            ))
    return chunks


def extract_page_for_chunk(chunk_text: str, full_text: str, start_index: int) -> int:
    """
    Find the actual page number for a chunk by looking for the last [Page X] marker 
    before or within the chunk.
    """
    # Look for all [Page X] markers before the end of the chunk
    matches = list(re.finditer(r"\[Page (\d+)\]", full_text[:start_index + len(chunk_text)]))
    if matches:
        # Get the last marker that appears before or at the start of the chunk
        # If the chunk starts with a marker, we use it.
        # If there are markers inside the chunk, the first one is usually the most representative
        # but the standard approach is to use the page where the chunk starts.

        last_marker_before_or_at_start = None
        for m in matches:
            if m.start() <= start_index:
                last_marker_before_or_at_start = m
            else:
                break

        if last_marker_before_or_at_start:
            return int(last_marker_before_or_at_start.group(1))

        # If no marker before start, but one inside, use the first one inside
        return int(matches[0].group(1))

    return 1