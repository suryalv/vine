from __future__ import annotations

"""
Tests for layers/parsing/parser.py
Validates PDF and DOCX extraction against real sample documents.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure backend root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from layers.parsing.parser import parse_pdf, parse_docx, parse_document


# ─── PDF Parsing ──────────────────────────────────────────────────


class TestParsePdf:
    """Tests for parse_pdf using real sample PDFs."""

    def test_parse_pdf_returns_list_of_tuples(self, sample_pdf_path):
        pages = parse_pdf(sample_pdf_path)
        assert isinstance(pages, list)
        assert len(pages) > 0
        for item in pages:
            assert isinstance(item, tuple)
            assert len(item) == 2

    def test_parse_pdf_page_numbers_start_at_one(self, sample_pdf_path):
        pages = parse_pdf(sample_pdf_path)
        first_page_num = pages[0][0]
        assert first_page_num == 1

    def test_parse_pdf_page_numbers_are_sequential(self, sample_pdf_path):
        pages = parse_pdf(sample_pdf_path)
        page_nums = [p[0] for p in pages]
        # Page numbers should be monotonically non-decreasing
        for i in range(1, len(page_nums)):
            assert page_nums[i] >= page_nums[i - 1]

    def test_parse_pdf_text_not_empty(self, sample_pdf_path):
        pages = parse_pdf(sample_pdf_path)
        for page_num, text in pages:
            assert isinstance(text, str)
            assert len(text.strip()) > 0, f"Page {page_num} has empty text"

    def test_parse_all_sample_pdfs(self, all_sample_pdf_paths):
        """Ensure all sample PDFs parse without error and yield content."""
        for pdf_path in all_sample_pdf_paths:
            pages = parse_pdf(pdf_path)
            assert len(pages) > 0, f"No pages extracted from {pdf_path}"
            total_text = " ".join(t for _, t in pages)
            assert len(total_text) > 50, f"Very little text from {pdf_path}"

    def test_parse_pdf_nonexistent_file_raises(self):
        with pytest.raises(Exception):
            parse_pdf("/nonexistent/path/fake.pdf")


# ─── DOCX Parsing ─────────────────────────────────────────────────


class TestParseDocx:
    """Tests for parse_docx using real sample DOCX files."""

    def test_parse_docx_returns_list_of_tuples(self, sample_docx_path):
        pages = parse_docx(sample_docx_path)
        assert isinstance(pages, list)
        assert len(pages) > 0
        for item in pages:
            assert isinstance(item, tuple)
            assert len(item) == 2

    def test_parse_docx_page_numbers_start_at_one(self, sample_docx_path):
        pages = parse_docx(sample_docx_path)
        assert pages[0][0] == 1

    def test_parse_docx_synthesized_page_numbers(self, sample_docx_path):
        """DOCX synthesizes pages at ~40 paragraphs each; verify page_num logic."""
        pages = parse_docx(sample_docx_path)
        page_nums = [p[0] for p in pages]
        for i in range(1, len(page_nums)):
            assert page_nums[i] >= page_nums[i - 1]

    def test_parse_docx_text_not_empty(self, sample_docx_path):
        pages = parse_docx(sample_docx_path)
        for page_num, text in pages:
            assert isinstance(text, str)
            assert len(text.strip()) > 0

    def test_parse_all_sample_docx(self, all_sample_docx_paths):
        for docx_path in all_sample_docx_paths:
            pages = parse_docx(docx_path)
            assert len(pages) > 0, f"No pages from {docx_path}"

    def test_parse_docx_nonexistent_raises(self):
        with pytest.raises(Exception):
            parse_docx("/nonexistent/fake.docx")


# ─── Auto-detection (parse_document) ──────────────────────────────


class TestParseDocument:
    """Tests for the auto-detecting parse_document function."""

    def test_auto_detect_pdf(self, sample_pdf_path):
        pages = parse_document(sample_pdf_path)
        assert len(pages) > 0

    def test_auto_detect_docx(self, sample_docx_path):
        pages = parse_document(sample_docx_path)
        assert len(pages) > 0

    def test_unsupported_extension_raises(self, tmp_dir):
        fake = os.path.join(tmp_dir, "report.txt")
        with open(fake, "w") as f:
            f.write("hello")
        with pytest.raises(ValueError, match="Unsupported file format"):
            parse_document(fake)

    def test_doc_extension_routes_to_docx(self, sample_docx_path, tmp_dir):
        """A .doc extension should also be handled via the docx branch."""
        # Copy sample docx with .doc extension
        import shutil
        doc_path = os.path.join(tmp_dir, "test.doc")
        shutil.copy(sample_docx_path, doc_path)
        pages = parse_document(doc_path)
        assert len(pages) > 0

    def test_case_insensitive_extension(self, sample_pdf_path, tmp_dir):
        """Extensions like .PDF should still work (lowered internally)."""
        import shutil
        upper_path = os.path.join(tmp_dir, "REPORT.PDF")
        shutil.copy(sample_pdf_path, upper_path)
        pages = parse_document(upper_path)
        assert len(pages) > 0


# ─── Content quality checks ──────────────────────────────────────


class TestParsingContentQuality:
    """Spot-check that parsed content has reasonable structure."""

    def test_pdf_contains_recognizable_text(self, all_sample_pdf_paths):
        """Sample UW PDFs should contain recognizable insurance terms."""
        insurance_terms = {"policy", "coverage", "insured", "premium", "loss", "claim", "limit"}
        for pdf_path in all_sample_pdf_paths:
            pages = parse_pdf(pdf_path)
            full_text = " ".join(t for _, t in pages).lower()
            found = {term for term in insurance_terms if term in full_text}
            assert len(found) >= 2, (
                f"{Path(pdf_path).name} has no recognizable insurance terms. "
                f"Found: {found}"
            )

    def test_docx_contains_recognizable_text(self, all_sample_docx_paths):
        insurance_terms = {"policy", "coverage", "insured", "endorsement", "limit", "value", "location"}
        for docx_path in all_sample_docx_paths:
            pages = parse_docx(docx_path)
            full_text = " ".join(t for _, t in pages).lower()
            found = {term for term in insurance_terms if term in full_text}
            assert len(found) >= 2, (
                f"{Path(docx_path).name} has no recognizable insurance terms. "
                f"Found: {found}"
            )
