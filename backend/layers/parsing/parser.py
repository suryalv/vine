from __future__ import annotations

"""
PARSING LAYER
=============
Extracts structured text from PDF and DOCX files.
Returns list of (page_number, text) tuples to preserve page provenance.

Team Owner: Document Ingestion Team
"""

from pathlib import Path
from PyPDF2 import PdfReader
from docx import Document as DocxDocument


def parse_pdf(filepath: str) -> list[tuple[int, str]]:
    """Extract text per page from a PDF file."""
    reader = PdfReader(filepath)
    pages: list[tuple[int, str]] = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            pages.append((i, text))
    return pages


def parse_docx(filepath: str) -> list[tuple[int, str]]:
    """
    Extract text from a DOCX file.
    DOCX doesn't have native page numbers, so we synthesize page breaks
    based on paragraph count (~40 paragraphs = 1 page).
    """
    doc = DocxDocument(filepath)
    full_paragraphs: list[str] = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            full_paragraphs.append(text)

    # Also extract table content
    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                full_paragraphs.append(" | ".join(cells))

    # Synthesize pages (~40 paragraphs per page)
    PAGE_SIZE = 40
    pages: list[tuple[int, str]] = []
    for i in range(0, len(full_paragraphs), PAGE_SIZE):
        page_num = (i // PAGE_SIZE) + 1
        page_text = "\n".join(full_paragraphs[i : i + PAGE_SIZE])
        if page_text.strip():
            pages.append((page_num, page_text))

    return pages


def parse_document(filepath: str) -> list[tuple[int, str]]:
    """Auto-detect format and parse."""
    ext = Path(filepath).suffix.lower()
    if ext == ".pdf":
        return parse_pdf(filepath)
    elif ext in (".docx", ".doc"):
        return parse_docx(filepath)
    else:
        raise ValueError(f"Unsupported file format: {ext}")
