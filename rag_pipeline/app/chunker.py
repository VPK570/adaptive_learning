"""Text chunking utilities — 512-token sentence-aware chunking."""

import re


def token_count(text: str) -> int:
    return len(text.split())


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
        sentence_tokens = len(sentence.split())
        total_after = current_token_count + sentence_tokens + len(current_sentences)

        if total_after > chunk_size and current_sentences:
            chunk_text_str = " ".join(current_sentences)
            chunks.append((chunk_text_str, start_char, start_char + len(chunk_text_str)))

            overlap_count = min(len(current_sentences), 3)
            if overlap_count > 0:
                overlap_sents = current_sentences[-overlap_count:]
                current_sentences = overlap_sents
                current_token_count = sum(len(s.split()) for s in overlap_sents)
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
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", text)
    text = re.sub(r"\bPage\s+\d+\b", "", text)
    text = re.sub(r"-\n", "", text)
    return text.strip()


def extract_page_for_chunk(chunk_text: str, original_text: str) -> int | None:
    page_markers = [m.start() for m in re.finditer(r"\f|\\pagebreak|Page \d+", original_text)]
    for i, marker in enumerate(page_markers):
        if marker > len(original_text) - len(chunk_text):
            return i + 1
    return 1