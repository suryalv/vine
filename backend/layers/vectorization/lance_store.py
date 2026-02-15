from __future__ import annotations

"""
VECTORIZATION LAYER — LanceDB Backend
======================================
LanceDB in-memory vector store for document chunk embeddings.
Handles storage, search, and document management.

Team Owner: Data Infrastructure Team
"""

from typing import List, Dict

import lancedb
import numpy as np

from config import LANCE_DB_PATH, LANCE_TABLE_NAME, TOP_K_RESULTS
from layers.embedding import embed_texts, embed_query
from layers.vectorization.base import VectorStore


class LanceDBStore(VectorStore):
    """LanceDB-backed vector store implementation."""

    def __init__(
        self,
        db_path: str = LANCE_DB_PATH,
        table_name: str = LANCE_TABLE_NAME,
        top_k: int = TOP_K_RESULTS,
    ):
        self._db_path = db_path
        self._table_name = table_name
        self._top_k = top_k
        self._db: lancedb.DBConnection | None = None
        self._document_registry: Dict[str, Dict] = {}
        self._registry_loaded = False

    def _get_db(self) -> lancedb.DBConnection:
        if self._db is None:
            self._db = lancedb.connect(self._db_path)
        return self._db

    def _table_exists(self) -> bool:
        db = self._get_db()
        return self._table_name in db.table_names()

    def _rebuild_registry(self) -> None:
        """Rebuild document registry from LanceDB data on startup."""
        if self._registry_loaded:
            return
        self._registry_loaded = True
        if not self._table_exists():
            return
        db = self._get_db()
        table = db.open_table(self._table_name)
        try:
            rows = table.search().limit(100000).to_list()
        except Exception:
            return
        doc_map: Dict[str, Dict] = {}
        for row in rows:
            doc_id = row.get("document_id", "")
            if not doc_id:
                continue
            if doc_id not in doc_map:
                doc_map[doc_id] = {
                    "document_id": doc_id,
                    "filename": row.get("source", "unknown"),
                    "num_chunks": 0,
                    "num_pages": 0,
                    "pages_seen": set(),
                }
            doc_map[doc_id]["num_chunks"] += 1
            page = row.get("page", 0)
            if page:
                doc_map[doc_id]["pages_seen"].add(page)
        for doc_id, info in doc_map.items():
            info["num_pages"] = len(info.pop("pages_seen"))
            self._document_registry[doc_id] = info

    def store_chunks(
        self, chunks: List[Dict], document_id: str, filename: str, num_pages: int
    ) -> int:
        """Embed and store document chunks in LanceDB."""
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

        db = self._get_db()
        if self._table_exists():
            table = db.open_table(self._table_name)
            table.add(records)
        else:
            db.create_table(self._table_name, data=records)

        self._document_registry[document_id] = {
            "document_id": document_id,
            "filename": filename,
            "num_chunks": len(chunks),
            "num_pages": num_pages,
        }
        return len(records)

    def search(self, query: str, top_k: int = None) -> List[Dict]:
        """Search for chunks most similar to the query."""
        if top_k is None:
            top_k = self._top_k
        if not self._table_exists():
            return []

        query_embedding = embed_query(query)
        db = self._get_db()
        table = db.open_table(self._table_name)

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

    def get_all_documents(self) -> List[Dict]:
        self._rebuild_registry()
        return list(self._document_registry.values())

    def delete_document(self, document_id: str) -> bool:
        if not self._table_exists():
            return False
        db = self._get_db()
        table = db.open_table(self._table_name)
        table.delete(f'document_id = "{document_id}"')
        self._document_registry.pop(document_id, None)
        return True

    def get_chunks_by_document(self, document_id: str) -> List[Dict]:
        if not self._table_exists():
            return []
        db = self._get_db()
        table = db.open_table(self._table_name)
        results = table.search().where(f'document_id = "{document_id}"').limit(1000).to_list()
        return [
            {"text": row["text"], "source": row["source"], "page": row["page"], "vector": row["vector"]}
            for row in results
        ]


# ─── Backward-compatible module-level API ────────────────────────
# Existing tests import directly from this module. These aliases
# delegate to a default singleton instance.

_default_store = LanceDBStore()

# Expose internal state for test fixtures that patch module globals
_db = _default_store._db
_document_registry = _default_store._document_registry
_registry_loaded = _default_store._registry_loaded


def _get_db():
    return _default_store._get_db()


def _table_exists():
    return _default_store._table_exists()


def store_chunks(chunks, document_id, filename, num_pages):
    return _default_store.store_chunks(chunks, document_id, filename, num_pages)


def search(query, top_k=TOP_K_RESULTS):
    return _default_store.search(query, top_k)


def get_all_documents():
    return _default_store.get_all_documents()


def delete_document(document_id):
    return _default_store.delete_document(document_id)


def get_chunks_by_document(document_id):
    return _default_store.get_chunks_by_document(document_id)
