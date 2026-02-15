from __future__ import annotations

"""
GUIDELINES ENFORCEMENT ENGINE
==============================
Checks submission documents against stored underwriting guidelines.
Retrieves relevant guideline chunks, uses LLM to evaluate compliance,
and returns structured enforcement findings.

Team Owner: Underwriting Rules Team
"""

import json
from typing import List

from models.schemas import GuidelineViolation, EnforcementReport
from layers.guidelines.guidelines_store import get_guidelines_store
from layers.vectorization import get_chunks_by_document, get_all_documents
from layers.generation.llm_factory import get_llm_provider


def _build_submission_summary(chunks: List[dict], max_chunks: int = 15) -> str:
    """Build a text summary from submission document chunks."""
    parts = []
    for i, chunk in enumerate(chunks[:max_chunks], 1):
        source = chunk.get("source", "unknown")
        page = chunk.get("page", 0)
        text = chunk.get("text", "")
        parts.append(f"[Submission — {source}, Page {page}]\n{text}")
    return "\n\n---\n\n".join(parts)


def _build_guidelines_context(guideline_chunks: List[dict]) -> str:
    """Build guideline context block for the enforcement prompt."""
    parts = []
    for i, chunk in enumerate(guideline_chunks, 1):
        source = chunk.get("source", "unknown")
        page = chunk.get("page", 0)
        section = chunk.get("section", "")
        text = chunk.get("text", "")
        header = f"[Guideline {i}: {source}, Page {page}"
        if section:
            header += f", Section: {section}"
        header += "]"
        parts.append(f"{header}\n{text}")
    return "\n\n---\n\n".join(parts)


def enforce_guidelines(
    document_id: str,
    line_of_business: str | None = None,
) -> EnforcementReport:
    """
    Check a submission document against stored UW guidelines.

    1. Retrieve submission chunks from the document store
    2. Search guidelines store for relevant rules
    3. Use LLM to compare and generate compliance findings
    4. Return structured EnforcementReport
    """
    # 1. Get submission document chunks
    submission_chunks = get_chunks_by_document(document_id)
    if not submission_chunks:
        raise ValueError(f"No chunks found for document_id: {document_id}")

    # Get document name
    all_docs = get_all_documents()
    doc_name = "Unknown Document"
    for doc in all_docs:
        if doc["document_id"] == document_id:
            doc_name = doc["filename"]
            break

    # 2. Build submission summary for guideline search
    submission_text = " ".join(
        chunk.get("text", "")[:200] for chunk in submission_chunks[:10]
    )

    # 3. Search guidelines
    store = get_guidelines_store()
    if line_of_business:
        guideline_chunks = store.search_by_line(
            submission_text, line_of_business, top_k=15
        )
    else:
        guideline_chunks = store.search_guidelines(submission_text, top_k=15)

    if not guideline_chunks:
        return EnforcementReport(
            document_id=document_id,
            document_name=doc_name,
            line_of_business=line_of_business or "all",
            num_guidelines_checked=0,
            num_violations=0,
            num_warnings=0,
            num_compliant=0,
            compliance_score=100.0,
            violations=[],
            summary="No underwriting guidelines are loaded. Upload guidelines to enable enforcement.",
        )

    # 4. Build prompts
    submission_summary = _build_submission_summary(submission_chunks)
    guidelines_context = _build_guidelines_context(guideline_chunks)

    prompt = f"""You are an underwriting compliance engine. Compare the submission document against the underwriting guidelines and identify any violations, warnings, or compliant items.

SUBMISSION DOCUMENT:
{submission_summary}

UNDERWRITING GUIDELINES:
{guidelines_context}

INSTRUCTIONS:
1. For each guideline rule that is relevant to this submission, evaluate whether the submission complies.
2. Classify each finding as:
   - "violation" — The submission clearly fails to meet the guideline requirement
   - "warning" — The submission is borderline or needs additional information to confirm compliance
   - "compliant" — The submission meets the guideline requirement
3. For violations and warnings, provide the specific data from the submission that triggered the finding.
4. Provide a brief recommendation for each finding.

Return a JSON object with this structure:
{{
  "findings": [
    {{
      "rule": "The specific guideline rule text",
      "status": "violation|warning|compliant",
      "finding": "What was found in the submission",
      "guideline_reference": "Source guideline document, section",
      "recommendation": "What the underwriter should do"
    }}
  ],
  "summary": "2-3 sentence executive summary of the compliance assessment"
}}

Return ONLY valid JSON, no markdown fences.
"""

    # 5. Call LLM
    llm = get_llm_provider()
    raw = llm.generate_simple(prompt)

    # 6. Parse response
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return EnforcementReport(
            document_id=document_id,
            document_name=doc_name,
            line_of_business=line_of_business or "all",
            num_guidelines_checked=len(guideline_chunks),
            num_violations=0,
            num_warnings=0,
            num_compliant=0,
            compliance_score=50.0,
            violations=[],
            summary="Could not parse LLM response for guideline enforcement.",
        )

    findings = data.get("findings", [])
    summary = data.get("summary", "")

    valid_statuses = {"violation", "warning", "compliant"}
    violations: list[GuidelineViolation] = []
    num_violations = 0
    num_warnings = 0
    num_compliant = 0

    for item in findings:
        status = item.get("status", "warning")
        if status not in valid_statuses:
            status = "warning"

        if status == "violation":
            num_violations += 1
        elif status == "warning":
            num_warnings += 1
        else:
            num_compliant += 1

        violations.append(
            GuidelineViolation(
                rule=item.get("rule", "Unknown rule"),
                status=status,
                finding=item.get("finding", ""),
                guideline_reference=item.get("guideline_reference", ""),
                recommendation=item.get("recommendation", ""),
            )
        )

    total = num_violations + num_warnings + num_compliant
    if total > 0:
        compliance_score = (num_compliant / total) * 100.0
        # Warnings count as half-compliant
        compliance_score = ((num_compliant + num_warnings * 0.5) / total) * 100.0
    else:
        compliance_score = 100.0

    compliance_score = round(min(100.0, max(0.0, compliance_score)), 1)

    return EnforcementReport(
        document_id=document_id,
        document_name=doc_name,
        line_of_business=line_of_business or "all",
        num_guidelines_checked=len(guideline_chunks),
        num_violations=num_violations,
        num_warnings=num_warnings,
        num_compliant=num_compliant,
        compliance_score=compliance_score,
        violations=violations,
        summary=summary,
    )
