from pydantic import BaseModel, Field
from typing import List, Optional


class ChatRequest(BaseModel):
    query: str
    session_id: str = "default"


class SourceReference(BaseModel):
    text: str
    source: str
    page: int
    similarity: float


class SentenceGrounding(BaseModel):
    sentence: str
    grounding_score: float
    best_source: str
    is_grounded: bool


class HallucinationReport(BaseModel):
    overall_score: float = Field(ge=0, le=100, description="0=hallucinated, 100=fully grounded")
    retrieval_confidence: float
    response_grounding: float
    numerical_fidelity: float
    entity_consistency: float
    sentence_details: List[SentenceGrounding]
    flagged_claims: List[str]
    rating: str  # "high", "medium", "low" risk


class UWAction(BaseModel):
    action: str
    category: str  # "coverage_gap", "risk_flag", "endorsement", "compliance", "pricing"
    priority: str  # "critical", "high", "medium", "low"
    details: str
    source_reference: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceReference]
    hallucination: HallucinationReport
    actions: List[UWAction]
    session_id: str


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    num_chunks: int
    num_pages: int
    status: str


class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    num_chunks: int
    num_pages: int
    upload_time: str


# ─── UW Guidelines ────────────────────────────────────────────────


class GuidelineViolation(BaseModel):
    rule: str
    status: str  # "violation", "warning", "compliant"
    finding: str
    guideline_reference: str
    recommendation: str


class EnforcementReport(BaseModel):
    document_id: str
    document_name: str
    line_of_business: str
    num_guidelines_checked: int
    num_violations: int
    num_warnings: int
    num_compliant: int
    compliance_score: float = Field(ge=0, le=100)
    violations: List[GuidelineViolation]
    summary: str


class GuidelineInfo(BaseModel):
    guideline_id: str
    filename: str
    line_of_business: str
    num_chunks: int
    num_pages: int
    upload_time: str


class GuidelineUploadResponse(BaseModel):
    guideline_id: str
    filename: str
    line_of_business: str
    num_chunks: int
    num_pages: int
    status: str


class EnforcementRequest(BaseModel):
    document_id: str
    line_of_business: Optional[str] = None
