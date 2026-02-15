from __future__ import annotations

"""
UW Companion Backend — FastAPI application
Provides document upload, RAG chat, and hallucination analysis endpoints.
"""

import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Ensure project root is on path for imports
sys.path.insert(0, os.path.dirname(__file__))

from models.schemas import (
    ChatRequest,
    ChatResponse,
    DocumentUploadResponse,
    DocumentInfo,
    SourceReference,
)
from layers.parsing import parse_document
from layers.chunking import chunk_document
from layers.vectorization import store_chunks, search, get_all_documents, delete_document
from layers.generation import generate_rag_response
from layers.hallucination import analyze_hallucination
from layers.actions import get_uw_actions
from config import (
    GEMINI_API_KEY,
    CORS_ORIGINS,
    LLM_BACKEND,
    EMBEDDING_BACKEND,
    VECTOR_STORE_BACKEND,
    API_HOST,
    API_PORT,
)

app = FastAPI(
    title="UW Companion API",
    description="AI-powered underwriting document analysis with hallucination detection",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("/tmp/uw_companion_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# In-memory chat history per session
_chat_history: dict[str, list[dict]] = {}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "llm_backend": LLM_BACKEND,
        "embedding_backend": EMBEDDING_BACKEND,
        "vector_store_backend": VECTOR_STORE_BACKEND,
        "gemini_configured": bool(GEMINI_API_KEY),
    }


# ─── Document Upload ─────────────────────────────────────────────

@app.post("/api/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload a PDF or DOCX, parse it, chunk it, and store embeddings in LanceDB."""
    if not file.filename:
        raise HTTPException(400, "No filename provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in (".pdf", ".docx", ".doc"):
        raise HTTPException(400, f"Unsupported file type: {ext}. Use PDF or DOCX.")

    # Save uploaded file to disk
    document_id = str(uuid.uuid4())
    save_path = UPLOAD_DIR / f"{document_id}{ext}"

    with open(save_path, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        # Parse document into pages
        pages = parse_document(str(save_path))
        if not pages:
            raise HTTPException(400, "Could not extract any text from the document")

        # Chunk the document
        chunks = chunk_document(pages, file.filename)

        # Store in vector DB
        chunk_dicts = [
            {
                "chunk_id": c.chunk_id,
                "text": c.text,
                "source": c.source,
                "page": c.page,
                "section": c.section,
            }
            for c in chunks
        ]

        num_stored = store_chunks(chunk_dicts, document_id, file.filename, len(pages))

        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            num_chunks=num_stored,
            num_pages=len(pages),
            status="indexed",
        )

    except HTTPException:
        raise
    except RuntimeError as e:
        if "GEMINI_API_KEY" in str(e):
            raise HTTPException(500, "GEMINI_API_KEY not configured on server")
        raise HTTPException(500, str(e))
    except Exception as e:
        raise HTTPException(500, f"Processing failed: {str(e)}")


# ─── Document Management ─────────────────────────────────────────

@app.get("/api/documents", response_model=List[DocumentInfo])
def list_documents():
    """List all uploaded documents."""
    docs = get_all_documents()
    return [
        DocumentInfo(
            document_id=d["document_id"],
            filename=d["filename"],
            num_chunks=d["num_chunks"],
            num_pages=d["num_pages"],
            upload_time=datetime.now(timezone.utc).isoformat(),
        )
        for d in docs
    ]


@app.delete("/api/documents/{document_id}")
def remove_document(document_id: str):
    """Remove a document and its chunks from the vector store."""
    success = delete_document(document_id)
    if not success:
        raise HTTPException(404, "Document not found")
    # Also remove the uploaded file
    for f in UPLOAD_DIR.glob(f"{document_id}.*"):
        f.unlink(missing_ok=True)
    return {"status": "deleted", "document_id": document_id}


@app.post("/api/documents/bulk-delete")
def bulk_delete_documents(document_ids: List[str]):
    """Delete multiple documents by their IDs."""
    results = []
    for doc_id in document_ids:
        success = delete_document(doc_id)
        if success:
            for f in UPLOAD_DIR.glob(f"{doc_id}.*"):
                f.unlink(missing_ok=True)
        results.append({"document_id": doc_id, "deleted": success})
    return {"results": results}


# ─── RAG Chat ────────────────────────────────────────────────────

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    RAG chat endpoint:
    1. Search LanceDB for relevant chunks
    2. Generate Gemini response grounded in context
    3. Run hallucination detection
    4. Extract underwriting actions
    """
    if not req.query.strip():
        raise HTTPException(400, "Query cannot be empty")

    try:
        # 1. Retrieve relevant chunks
        source_chunks = search(req.query)

        if not source_chunks:
            return ChatResponse(
                answer="No documents have been uploaded yet. Please upload underwriting documents first, then ask your question.",
                sources=[],
                hallucination={
                    "overall_score": 0,
                    "retrieval_confidence": 0,
                    "response_grounding": 0,
                    "numerical_fidelity": 0,
                    "entity_consistency": 0,
                    "sentence_details": [],
                    "flagged_claims": [],
                    "rating": "high",
                },
                actions=[],
                session_id=req.session_id,
            )

        # 2. Get chat history for this session
        history = _chat_history.get(req.session_id, [])

        # 3. Generate RAG response
        answer = generate_rag_response(req.query, source_chunks, history)

        # 4. Run hallucination detection
        hallucination_report = analyze_hallucination(answer, source_chunks, req.query)

        # 5. Extract UW actions
        actions = get_uw_actions(req.query, answer, source_chunks)

        # 6. Update chat history
        if req.session_id not in _chat_history:
            _chat_history[req.session_id] = []
        _chat_history[req.session_id].append({"role": "user", "content": req.query})
        _chat_history[req.session_id].append({"role": "assistant", "content": answer})

        # Keep history manageable (last 20 messages)
        if len(_chat_history[req.session_id]) > 20:
            _chat_history[req.session_id] = _chat_history[req.session_id][-20:]

        # Build source references
        sources = [
            SourceReference(
                text=c["text"][:300],
                source=c["source"],
                page=c["page"],
                similarity=round(c["similarity"], 3),
            )
            for c in source_chunks[:5]
        ]

        return ChatResponse(
            answer=answer,
            sources=sources,
            hallucination=hallucination_report,
            actions=actions,
            session_id=req.session_id,
        )

    except RuntimeError as e:
        if "GEMINI_API_KEY" in str(e):
            raise HTTPException(500, "GEMINI_API_KEY not configured on server")
        raise HTTPException(500, str(e))


# ─── Hallucination Analysis (standalone) ─────────────────────────

@app.post("/api/hallucination/analyze")
async def analyze_response_hallucination(
    response_text: str,
    query: str,
    top_k: int = 8,
):
    """Standalone hallucination analysis for any response text against stored documents."""
    source_chunks = search(query, top_k)
    if not source_chunks:
        raise HTTPException(400, "No documents indexed — upload documents first")

    report = analyze_hallucination(response_text, source_chunks, query)
    return report


# ─── Session Management ──────────────────────────────────────────

@app.delete("/api/chat/session/{session_id}")
def clear_session(session_id: str):
    """Clear chat history for a session."""
    _chat_history.pop(session_id, None)
    return {"status": "cleared", "session_id": session_id}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=API_HOST, port=API_PORT, reload=True)
