from __future__ import annotations

"""
Smart document chunker for underwriting documents.

Strategy:
  1. Split by section headers (common in policies/endorsements)
  2. Fall back to paragraph-level splitting
  3. Recursive sentence splitting for oversized chunks
  4. Overlap between adjacent chunks for context continuity
"""

import re
import uuid
from dataclasses import dataclass, field

from config import CHUNK_SIZE, CHUNK_OVERLAP


@dataclass
class Chunk:
    chunk_id: str
    text: str
    source: str
    page: int
    section: str = ""
    token_estimate: int = 0

    def __post_init__(self):
        self.token_estimate = len(self.text.split())


# Patterns that likely indicate section headers in UW documents
SECTION_PATTERNS = [
    r"^(?:SECTION|PART|ARTICLE|SCHEDULE|FORM|ENDORSEMENT)\s+[A-Z0-9]+",
    r"^[A-Z][A-Z\s]{5,}$",  # ALL CAPS lines
    r"^\d+\.\s+[A-Z]",  # Numbered sections
    r"^(?:I{1,3}|IV|V|VI{1,3}|IX|X)\.\s+",  # Roman numerals
]


def _is_section_header(line: str) -> bool:
    line = line.strip()
    if not line or len(line) > 120:
        return False
    for pattern in SECTION_PATTERNS:
        if re.match(pattern, line):
            return True
    return False


def _split_into_sections(text: str) -> list[tuple[str, str]]:
    """Split text into (section_header, section_body) pairs."""
    lines = text.split("\n")
    sections: list[tuple[str, str]] = []
    current_header = ""
    current_lines: list[str] = []

    for line in lines:
        if _is_section_header(line):
            if current_lines:
                sections.append((current_header, "\n".join(current_lines)))
            current_header = line.strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_header, "\n".join(current_lines)))

    return sections


def _split_by_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def _recursive_chunk(text: str, max_tokens: int) -> list[str]:
    """Recursively split text to fit within max_tokens."""
    words = text.split()
    if len(words) <= max_tokens:
        return [text] if text.strip() else []

    # Try splitting by paragraphs first
    paragraphs = text.split("\n\n")
    if len(paragraphs) > 1:
        chunks = []
        current = ""
        for para in paragraphs:
            candidate = (current + "\n\n" + para).strip() if current else para
            if len(candidate.split()) <= max_tokens:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                # If single paragraph is too big, split by sentences
                if len(para.split()) > max_tokens:
                    chunks.extend(_recursive_chunk(para, max_tokens))
                else:
                    current = para
        if current:
            chunks.append(current)
        return chunks

    # Split by sentences
    sentences = _split_by_sentences(text)
    if len(sentences) > 1:
        chunks = []
        current = ""
        for sent in sentences:
            candidate = (current + " " + sent).strip() if current else sent
            if len(candidate.split()) <= max_tokens:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                current = sent
        if current:
            chunks.append(current)
        return chunks

    # Hard split by word count as last resort
    chunks = []
    for i in range(0, len(words), max_tokens):
        chunks.append(" ".join(words[i : i + max_tokens]))
    return chunks


def _add_overlap(chunks: list[str], overlap_tokens: int) -> list[str]:
    """Add overlapping context between adjacent chunks."""
    if len(chunks) <= 1 or overlap_tokens == 0:
        return chunks

    overlapped: list[str] = [chunks[0]]
    for i in range(1, len(chunks)):
        prev_words = chunks[i - 1].split()
        overlap_text = " ".join(prev_words[-overlap_tokens:])
        overlapped.append(overlap_text + " " + chunks[i])
    return overlapped


def chunk_document(
    pages: list[tuple[int, str]],
    source_filename: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[Chunk]:
    """
    Chunk a parsed document into overlapping pieces.

    Args:
        pages: list of (page_number, page_text) from document parser
        source_filename: original filename for provenance
        chunk_size: target chunk size in tokens (words)
        chunk_overlap: overlap in tokens between adjacent chunks

    Returns:
        List of Chunk objects ready for embedding
    """
    all_chunks: list[Chunk] = []

    for page_num, page_text in pages:
        sections = _split_into_sections(page_text)

        for section_header, section_body in sections:
            if not section_body.strip():
                continue

            raw_chunks = _recursive_chunk(section_body, chunk_size)
            overlapped = _add_overlap(raw_chunks, chunk_overlap)

            for text in overlapped:
                if not text.strip():
                    continue
                # Prepend section header for context
                full_text = f"[{section_header}] {text}" if section_header else text
                all_chunks.append(
                    Chunk(
                        chunk_id=str(uuid.uuid4()),
                        text=full_text,
                        source=source_filename,
                        page=page_num,
                        section=section_header,
                    )
                )

    return all_chunks
