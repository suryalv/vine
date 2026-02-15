from __future__ import annotations

"""
API LAYER
=========
FastAPI route definitions. This module re-exports the FastAPI app
from main.py for use with uvicorn or other ASGI servers.

The API layer ties together all other layers:
  Parsing → Chunking → Embedding → Vectorization → Generation → Hallucination → Actions

Team Owner: Backend / API Team

Endpoints:
  POST   /api/documents/upload     Upload & index a PDF/DOCX
  GET    /api/documents             List all indexed documents
  DELETE /api/documents/{id}        Remove a document
  POST   /api/chat                  RAG chat with hallucination analysis
  DELETE /api/chat/session/{id}     Clear chat history
  POST   /api/hallucination/analyze Standalone hallucination check
  GET    /health                    Health check
"""

# Routes are defined in main.py — this file documents the API layer
# and provides a convenient import path.
#
# Usage:
#   uvicorn main:app --port 8000
#
# Or programmatically:
#   from layers.api.routes import ENDPOINT_MAP

ENDPOINT_MAP = {
    "upload_document": {
        "method": "POST",
        "path": "/api/documents/upload",
        "description": "Upload a PDF or DOCX file for parsing, chunking, and vector indexing",
        "layers_used": ["parsing", "chunking", "embedding", "vectorization"],
    },
    "list_documents": {
        "method": "GET",
        "path": "/api/documents",
        "description": "List all uploaded and indexed documents",
        "layers_used": ["vectorization"],
    },
    "delete_document": {
        "method": "DELETE",
        "path": "/api/documents/{document_id}",
        "description": "Remove a document and its chunks from the vector store",
        "layers_used": ["vectorization"],
    },
    "chat": {
        "method": "POST",
        "path": "/api/chat",
        "description": "RAG chat: retrieve → generate → hallucination check → extract actions",
        "layers_used": ["vectorization", "generation", "hallucination", "actions"],
    },
    "clear_session": {
        "method": "DELETE",
        "path": "/api/chat/session/{session_id}",
        "description": "Clear chat history for a session",
        "layers_used": [],
    },
    "hallucination_analyze": {
        "method": "POST",
        "path": "/api/hallucination/analyze",
        "description": "Standalone hallucination analysis for any response text",
        "layers_used": ["vectorization", "hallucination"],
    },
    "health": {
        "method": "GET",
        "path": "/health",
        "description": "Health check with Gemini configuration status",
        "layers_used": [],
    },
}
