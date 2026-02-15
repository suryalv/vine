from __future__ import annotations

"""
Tests for layers/chunking/chunker.py
The chunker is entirely local logic — no API calls — so we test thoroughly.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from layers.chunking.chunker import (
    Chunk,
    _is_section_header,
    _split_into_sections,
    _split_by_sentences,
    _recursive_chunk,
    _add_overlap,
    chunk_document,
    SECTION_PATTERNS,
)
from config import CHUNK_SIZE, CHUNK_OVERLAP


# ─── Chunk dataclass ──────────────────────────────────────────────


class TestChunkDataclass:
    def test_chunk_creates_with_required_fields(self):
        c = Chunk(chunk_id="abc", text="Hello world foo bar", source="test.pdf", page=1)
        assert c.chunk_id == "abc"
        assert c.text == "Hello world foo bar"
        assert c.source == "test.pdf"
        assert c.page == 1

    def test_chunk_token_estimate_calculated(self):
        c = Chunk(chunk_id="1", text="one two three four five", source="f.pdf", page=1)
        assert c.token_estimate == 5

    def test_chunk_default_section_empty(self):
        c = Chunk(chunk_id="1", text="text", source="f.pdf", page=1)
        assert c.section == ""

    def test_chunk_section_set(self):
        c = Chunk(chunk_id="1", text="text", source="f.pdf", page=1, section="SECTION A")
        assert c.section == "SECTION A"

    def test_chunk_token_estimate_empty_text(self):
        c = Chunk(chunk_id="1", text="", source="f.pdf", page=1)
        assert c.token_estimate == 0


# ─── Section header detection ─────────────────────────────────────


class TestIsSectionHeader:
    @pytest.mark.parametrize(
        "line",
        [
            "SECTION A GENERAL CONDITIONS",
            "PART 1 DEFINITIONS",
            "ARTICLE III EXCLUSIONS",
            "SCHEDULE 1 LOCATIONS",
            "ENDORSEMENT E100",
            "FORM CG0001",
            "GENERAL LIABILITY COVERAGE",
            "PROPERTY DAMAGE LIMITS",
            "1. Introduction",
            "2. Definitions",
            "I. Overview",
            "II. Scope",
            "III. Conditions",
            "IV. Exclusions",
        ],
    )
    def test_recognized_as_header(self, line):
        assert _is_section_header(line), f"Expected header: {line!r}"

    @pytest.mark.parametrize(
        "line",
        [
            "This is a normal sentence about coverage.",
            "the insured must comply with requirements",
            "Premium is $25,000 annually.",
            "",
            "   ",
            "a",
        ],
    )
    def test_not_recognized_as_header(self, line):
        assert not _is_section_header(line), f"Should not be header: {line!r}"

    def test_long_line_not_header(self):
        """Lines over 120 chars are rejected even if they match a pattern."""
        long_line = "SECTION A " + "X" * 120
        assert not _is_section_header(long_line)

    def test_empty_string(self):
        assert not _is_section_header("")

    def test_whitespace_only(self):
        assert not _is_section_header("   \t  ")


# ─── _split_into_sections ────────────────────────────────────────


class TestSplitIntoSections:
    def test_no_headers_single_section(self):
        text = "Line one.\nLine two.\nLine three."
        sections = _split_into_sections(text)
        assert len(sections) == 1
        assert sections[0][0] == ""  # no header
        assert "Line one" in sections[0][1]

    def test_multiple_headers_split(self):
        text = "SECTION A OVERVIEW\nThis is section A content.\nSECTION B DETAILS\nThis is section B content."
        sections = _split_into_sections(text)
        assert len(sections) == 2
        assert sections[0][0] == "SECTION A OVERVIEW"
        assert "section A content" in sections[0][1]
        assert sections[1][0] == "SECTION B DETAILS"
        assert "section B content" in sections[1][1]

    def test_content_before_first_header(self):
        text = "Some preamble text.\nSECTION A OVERVIEW\nContent after header."
        sections = _split_into_sections(text)
        assert len(sections) == 2
        assert sections[0][0] == ""  # preamble has no header
        assert "preamble" in sections[0][1]
        assert sections[1][0] == "SECTION A OVERVIEW"


# ─── _split_by_sentences ─────────────────────────────────────────


class TestSplitBySentences:
    def test_simple_split(self):
        text = "First sentence. Second sentence. Third sentence."
        sentences = _split_by_sentences(text)
        assert len(sentences) == 3

    def test_exclamation_and_question(self):
        text = "Is this covered? Yes it is! The policy applies."
        sentences = _split_by_sentences(text)
        assert len(sentences) == 3

    def test_single_sentence(self):
        text = "Only one sentence here."
        sentences = _split_by_sentences(text)
        assert len(sentences) == 1

    def test_empty_string(self):
        sentences = _split_by_sentences("")
        assert sentences == []

    def test_strips_whitespace(self):
        text = "  First sentence.   Second sentence.  "
        sentences = _split_by_sentences(text)
        for s in sentences:
            assert s == s.strip()


# ─── _recursive_chunk ─────────────────────────────────────────────


class TestRecursiveChunk:
    def test_small_text_single_chunk(self):
        text = "Short text here."
        chunks = _recursive_chunk(text, max_tokens=50)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_empty_text(self):
        chunks = _recursive_chunk("", max_tokens=50)
        assert chunks == []

    def test_whitespace_only(self):
        chunks = _recursive_chunk("   \n  \n  ", max_tokens=50)
        assert chunks == []

    def test_splits_large_text_by_paragraphs(self):
        para1 = "Word " * 30  # 30 tokens
        para2 = "Token " * 30
        text = para1.strip() + "\n\n" + para2.strip()
        chunks = _recursive_chunk(text, max_tokens=35)
        assert len(chunks) == 2

    def test_splits_by_sentences_when_no_paragraphs(self):
        text = "First sentence here. Second sentence here. Third sentence here. Fourth sentence here."
        chunks = _recursive_chunk(text, max_tokens=5)
        assert len(chunks) >= 2

    def test_hard_split_when_no_sentences(self):
        """A single long word-stream with no punctuation gets force-split."""
        text = " ".join(f"word{i}" for i in range(100))
        chunks = _recursive_chunk(text, max_tokens=20)
        assert len(chunks) >= 5
        for chunk in chunks:
            assert len(chunk.split()) <= 20

    def test_all_words_preserved(self):
        """Ensure no words are lost during recursive chunking."""
        text = " ".join(f"w{i}" for i in range(200))
        chunks = _recursive_chunk(text, max_tokens=30)
        reconstructed = " ".join(chunks)
        original_words = set(text.split())
        reconstructed_words = set(reconstructed.split())
        assert original_words == reconstructed_words

    def test_respects_max_tokens(self):
        text = "This is a longer paragraph. " * 50
        chunks = _recursive_chunk(text, max_tokens=20)
        for chunk in chunks:
            # Allow slight overflow due to sentence boundaries
            assert len(chunk.split()) <= 25, f"Chunk too large: {len(chunk.split())} words"


# ─── _add_overlap ─────────────────────────────────────────────────


class TestAddOverlap:
    def test_single_chunk_unchanged(self):
        chunks = ["Only one chunk here."]
        result = _add_overlap(chunks, overlap_tokens=10)
        assert result == chunks

    def test_zero_overlap(self):
        chunks = ["Chunk one.", "Chunk two."]
        result = _add_overlap(chunks, overlap_tokens=0)
        assert result == chunks

    def test_overlap_prepended_to_subsequent_chunks(self):
        chunks = ["alpha bravo charlie delta", "echo foxtrot golf hotel"]
        result = _add_overlap(chunks, overlap_tokens=2)
        assert len(result) == 2
        assert result[0] == "alpha bravo charlie delta"
        # Second chunk should start with last 2 words of first chunk
        assert result[1].startswith("charlie delta ")
        assert "echo foxtrot golf hotel" in result[1]

    def test_overlap_with_three_chunks(self):
        chunks = ["one two three four", "five six seven eight", "nine ten eleven twelve"]
        result = _add_overlap(chunks, overlap_tokens=2)
        assert len(result) == 3
        assert result[0] == "one two three four"
        assert result[1].startswith("three four ")
        assert result[2].startswith("seven eight ")

    def test_empty_list(self):
        result = _add_overlap([], overlap_tokens=5)
        assert result == []


# ─── chunk_document (integration) ─────────────────────────────────


class TestChunkDocument:
    def test_returns_list_of_chunks(self, sample_pages):
        chunks = chunk_document(sample_pages, "test.pdf")
        assert isinstance(chunks, list)
        assert all(isinstance(c, Chunk) for c in chunks)

    def test_chunks_have_required_fields(self, sample_pages):
        chunks = chunk_document(sample_pages, "test.pdf")
        for c in chunks:
            assert c.chunk_id  # non-empty UUID
            assert c.text
            assert c.source == "test.pdf"
            assert c.page >= 1

    def test_chunks_have_token_estimates(self, sample_pages):
        chunks = chunk_document(sample_pages, "test.pdf")
        for c in chunks:
            assert c.token_estimate > 0

    def test_section_headers_captured(self, sample_pages):
        chunks = chunk_document(sample_pages, "test.pdf")
        sections = {c.section for c in chunks}
        # Our sample_pages have "SECTION A GENERAL CONDITIONS" and "SECTION B LIABILITY"
        assert any("SECTION A" in s for s in sections)
        assert any("SECTION B" in s for s in sections)

    def test_section_header_prepended_to_text(self, sample_pages):
        chunks = chunk_document(sample_pages, "test.pdf")
        for c in chunks:
            if c.section:
                assert c.text.startswith(f"[{c.section}]")

    def test_empty_pages_produce_no_chunks(self):
        pages = [(1, ""), (2, "   ")]
        chunks = chunk_document(pages, "empty.pdf")
        assert len(chunks) == 0

    def test_custom_chunk_size(self, sample_pages):
        small_chunks = chunk_document(sample_pages, "test.pdf", chunk_size=10, chunk_overlap=2)
        large_chunks = chunk_document(sample_pages, "test.pdf", chunk_size=500, chunk_overlap=10)
        assert len(small_chunks) >= len(large_chunks)

    def test_unique_chunk_ids(self, sample_pages):
        chunks = chunk_document(sample_pages, "test.pdf")
        ids = [c.chunk_id for c in chunks]
        assert len(ids) == len(set(ids)), "Chunk IDs must be unique"

    def test_all_pages_represented(self, sample_pages):
        chunks = chunk_document(sample_pages, "test.pdf")
        pages_in_chunks = {c.page for c in chunks}
        pages_in_input = {p[0] for p in sample_pages}
        assert pages_in_chunks == pages_in_input

    def test_large_page_gets_split(self):
        """A page with lots of text should produce multiple chunks."""
        big_text = "This is a sentence about coverage. " * 200
        pages = [(1, big_text)]
        chunks = chunk_document(pages, "big.pdf", chunk_size=50, chunk_overlap=5)
        assert len(chunks) > 1

    def test_real_pdf_content_chunks(self, sample_pdf_path):
        """End-to-end: parse a real PDF then chunk it."""
        from layers.parsing.parser import parse_pdf

        pages = parse_pdf(sample_pdf_path)
        chunks = chunk_document(pages, Path(sample_pdf_path).name)
        assert len(chunks) > 0
        for c in chunks:
            assert c.source == Path(sample_pdf_path).name
            assert c.text.strip()

    def test_real_docx_content_chunks(self, sample_docx_path):
        """End-to-end: parse a real DOCX then chunk it."""
        from layers.parsing.parser import parse_docx

        pages = parse_docx(sample_docx_path)
        chunks = chunk_document(pages, Path(sample_docx_path).name)
        assert len(chunks) > 0


# ─── Config values sanity ─────────────────────────────────────────


class TestChunkingConfig:
    def test_chunk_size_is_positive(self):
        assert CHUNK_SIZE > 0

    def test_chunk_overlap_is_less_than_size(self):
        assert CHUNK_OVERLAP < CHUNK_SIZE

    def test_chunk_overlap_is_non_negative(self):
        assert CHUNK_OVERLAP >= 0
