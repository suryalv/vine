from __future__ import annotations

"""
Shared pytest fixtures for UW Companion backend tests.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

import pytest

# Ensure the backend root is on sys.path so all layer imports work
BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

# ─── Paths ────────────────────────────────────────────────────────

SAMPLE_DOCS_DIR = BACKEND_ROOT.parent / "sample-documents"

SAMPLE_PDFS = sorted(SAMPLE_DOCS_DIR.glob("*.pdf"))
SAMPLE_DOCX = sorted(SAMPLE_DOCS_DIR.glob("*.docx"))


# ─── Fixtures: sample file paths ──────────────────────────────────

@pytest.fixture
def sample_pdf_path() -> str:
    """Return path to the first sample PDF."""
    assert SAMPLE_PDFS, "No sample PDFs found in sample-documents/"
    return str(SAMPLE_PDFS[0])


@pytest.fixture
def sample_docx_path() -> str:
    """Return path to the first sample DOCX."""
    assert SAMPLE_DOCX, "No sample DOCX files found in sample-documents/"
    return str(SAMPLE_DOCX[0])


@pytest.fixture
def all_sample_pdf_paths() -> list[str]:
    """Return paths to all sample PDFs."""
    return [str(p) for p in SAMPLE_PDFS]


@pytest.fixture
def all_sample_docx_paths() -> list[str]:
    """Return paths to all sample DOCX files."""
    return [str(p) for p in SAMPLE_DOCX]


# ─── Fixtures: temporary directory ────────────────────────────────

@pytest.fixture
def tmp_dir():
    """Create a temporary directory that is cleaned up after the test."""
    d = tempfile.mkdtemp(prefix="uw_test_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


# ─── Fixtures: sample parsed pages ───────────────────────────────

@pytest.fixture
def sample_pages() -> list[tuple[int, str]]:
    """Synthetic parsed pages for chunking tests."""
    return [
        (1, "SECTION A GENERAL CONDITIONS\nThis policy covers commercial property.\nThe insured must comply with all safety requirements.\nPremium is based on property valuation."),
        (2, "Coverage includes fire, wind, and hail damage.\nExclusions apply to flood and earthquake.\nDeductible is $5,000 per occurrence."),
        (3, "SECTION B LIABILITY\nGeneral liability coverage is provided.\nLimits are $1,000,000 per occurrence and $2,000,000 aggregate.\nAdditional insured endorsements are available."),
    ]


# ─── Fixtures: source chunks for hallucination / action tests ────

@pytest.fixture
def sample_source_chunks() -> list[dict]:
    """Realistic source chunks as returned by vector search."""
    return [
        {
            "text": "The policy covers commercial property with limits of $1,000,000 per occurrence. "
                    "Premium is $25,000 annually. Deductible is $5,000. Policy number CP-2024-001.",
            "source": "Commercial_Property_Policy.pdf",
            "page": 1,
            "section": "COVERAGE SUMMARY",
            "similarity": 0.92,
            "document_id": "doc-001",
        },
        {
            "text": "Endorsement WH-100 amends wind and hail coverage. "
                    "Sub-limit of $500,000 applies. Effective date January 15, 2025. "
                    "Insured: Meridian Steel Works LLC.",
            "source": "Endorsement_Package.docx",
            "page": 2,
            "section": "WIND HAIL ENDORSEMENT",
            "similarity": 0.85,
            "document_id": "doc-002",
        },
        {
            "text": "Loss history shows 3 claims in the past 5 years totaling $150,000. "
                    "Largest single loss was $75,000 in March 2022. "
                    "Loss ratio is 35%.",
            "source": "Loss_Run_Report.pdf",
            "page": 3,
            "section": "LOSS SUMMARY",
            "similarity": 0.78,
            "document_id": "doc-003",
        },
    ]


# ─── Fixtures: mock embedding helper ─────────────────────────────

@pytest.fixture
def mock_embedding():
    """Return a callable that creates a deterministic fake embedding for a string."""
    import hashlib
    import numpy as np

    def _embed(text: str, dim: int = 768) -> list[float]:
        seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
        rng = np.random.RandomState(seed)
        vec = rng.randn(dim).astype(np.float32)
        vec = vec / np.linalg.norm(vec)
        return vec.tolist()

    return _embed
