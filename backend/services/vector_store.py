from __future__ import annotations

"""
LanceDB vector store — in-memory storage for document chunk embeddings.
"""

import lancedb
import numpy as np
import pyarrow as pa

from config import LANCE_DB_PATH, LANCE_TABLE_NAME, EMBEDDING_DIM, TOP_K_RESULTS
from services.gemini_service import embed_texts, embed_query

# Module-level connection (lazy init)
_db: lancedb.DBConnection | None = None
_document_registry: dict[str, dict] = {}


def _get_db() -> lancedb.DBConnection:
    global _db
    if _db is None:
        _db = lancedb.connect(LANCE_DB_PATH)
    return _db


def _table_exists() -> bool:
    db = _get_db()
    return LANCE_TABLE_NAME in db.table_names()


def store_chunks(
    chunks: list[dict],
    document_id: str,
    filename: str,
    num_pages: int,
) -> int:
    """
    Embed and store document chunks in LanceDB.

    Args:
        chunks: list of {chunk_id, text, source, page, section} dicts
        document_id: unique ID for this document
        filename: original filename
        num_pages: total pages in document

    Returns:
        Number of chunks stored
    """
    if not chunks:
        return 0

    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts)

    records = []
    for chunk, embedding in zip(chunks, embeddings):
        records.append(
            {
                "vector": np.array(embedding, dtype=np.float32),
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "source": chunk["source"],
                "page": chunk["page"],
                "section": chunk.get("section", ""),
                "document_id": document_id,
            }
        )

    db = _get_db()

    if _table_exists():
        table = db.open_table(LANCE_TABLE_NAME)
        table.add(records)
    else:
        db.create_table(LANCE_TABLE_NAME, data=records)

    # Register document metadata
    _document_registry[document_id] = {
        "document_id": document_id,
        "filename": filename,
        "num_chunks": len(chunks),
        "num_pages": num_pages,
    }

    return len(records)


def search(query: str, top_k: int = TOP_K_RESULTS) -> list[dict]:
    """
    Search for chunks most similar to the query.

    Returns:
        List of {text, source, page, section, similarity, document_id} dicts
    """
    if not _table_exists():
        return []

    query_embedding = embed_query(query)
    db = _get_db()
    table = db.open_table(LANCE_TABLE_NAME)

    results = (
        table.search(np.array(query_embedding, dtype=np.float32))
        .limit(top_k)
        .to_list()
    )

    output = []
    for row in results:
        output.append(
            {
                "text": row["text"],
                "source": row["source"],
                "page": row["page"],
                "section": row.get("section", ""),
                "similarity": 1.0 - float(row.get("_distance", 0)),
                "document_id": row["document_id"],
            }
        )

    return output


def get_all_documents() -> list[dict]:
    """Return metadata for all uploaded documents."""
    return list(_document_registry.values())


def delete_document(document_id: str) -> bool:
    """Delete all chunks for a given document."""
    if not _table_exists():
        return False

    db = _get_db()
    table = db.open_table(LANCE_TABLE_NAME)
    table.delete(f'document_id = "{document_id}"')
    _document_registry.pop(document_id, None)
    return True


def get_chunks_by_document(document_id: str) -> list[dict]:
    """Retrieve all chunks for a specific document (for hallucination checking)."""
    if not _table_exists():
        return []

    db = _get_db()
    table = db.open_table(LANCE_TABLE_NAME)
    results = table.search().where(f'document_id = "{document_id}"').limit(1000).to_list()

    return [
        {
            "text": row["text"],
            "source": row["source"],
            "page": row["page"],
            "vector": row["vector"],
        }
        for row in results
    ]
