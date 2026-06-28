"""Minimal, dependency-free text chunker for the documentation corpus."""

from __future__ import annotations


def chunk_text(text: str, max_chars: int = 900, overlap: int = 150) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)
        if len(para) <= max_chars:
            current = para
        else:
            # paragraph itself is too long; hard-split with overlap
            start = 0
            while start < len(para):
                end = start + max_chars
                chunks.append(para[start:end])
                start = end - overlap
            current = ""

    if current:
        chunks.append(current)

    if overlap and len(chunks) > 1:
        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_tail = chunks[i - 1][-overlap:]
            overlapped.append(prev_tail + "\n\n" + chunks[i])
        return overlapped

    return chunks
