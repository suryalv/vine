from __future__ import annotations

"""
GUIDELINES STORE
================
LanceDB-backed store for underwriting guidelines.
Uses a SEPARATE table ('uw_guidelines') from the document chunks table,
keeping guidelines isolated from regular document data.

Team Owner: Underwriting Rules Team
"""

from typing import List, Dict

import lancedb
import numpy as np

from config import LANCE_DB_PATH, GUIDELINES_TABLE_NAME, GUIDELINES_TOP_K
from layers.embedding import embed_texts, embed_query


class GuidelinesStore:
    """LanceDB-backed store for underwriting guideline chunks."""

    def __init__(
        self,
        db_path: str = LANCE_DB_PATH,
        table_name: str = GUIDELINES_TABLE_NAME,
        top_k: int = GUIDELINES_TOP_K,
    ):
        self._db_path = db_path
        self._table_name = table_name
        self._top_k = top_k
        self._db: lancedb.DBConnection | None = None
        self._guideline_registry: Dict[str, Dict] = {}
        self._registry_loaded = False

    def _get_db(self) -> lancedb.DBConnection:
        if self._db is None:
            self._db = lancedb.connect(self._db_path)
        return self._db

    def _table_exists(self) -> bool:
        db = self._get_db()
        return self._table_name in db.table_names()

    def _rebuild_registry(self) -> None:
        """Rebuild guideline registry from LanceDB data on startup."""
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
            gid = row.get("guideline_id", "")
            if not gid:
                continue
            if gid not in doc_map:
                doc_map[gid] = {
                    "guideline_id": gid,
                    "filename": row.get("source", "unknown"),
                    "line_of_business": row.get("line_of_business", ""),
                    "num_chunks": 0,
                    "num_pages": 0,
                    "pages_seen": set(),
                }
            doc_map[gid]["num_chunks"] += 1
            page = row.get("page", 0)
            if page:
                doc_map[gid]["pages_seen"].add(page)
        for gid, info in doc_map.items():
            info["num_pages"] = len(info.pop("pages_seen"))
            self._guideline_registry[gid] = info

    def store_guideline_chunks(
        self,
        chunks: List[Dict],
        guideline_id: str,
        filename: str,
        line_of_business: str,
        num_pages: int,
    ) -> int:
        """Embed and store guideline chunks in LanceDB."""
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
                    "guideline_id": guideline_id,
                    "line_of_business": line_of_business,
                }
            )

        db = self._get_db()
        if self._table_exists():
            table = db.open_table(self._table_name)
            table.add(records)
        else:
            db.create_table(self._table_name, data=records)

        self._guideline_registry[guideline_id] = {
            "guideline_id": guideline_id,
            "filename": filename,
            "line_of_business": line_of_business,
            "num_chunks": len(chunks),
            "num_pages": num_pages,
        }
        return len(records)

    def search_guidelines(self, query: str, top_k: int | None = None) -> List[Dict]:
        """Search for guideline chunks most similar to the query."""
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
                    "guideline_id": row["guideline_id"],
                    "line_of_business": row.get("line_of_business", ""),
                }
            )
        return output

    def search_by_line(
        self, query: str, line_of_business: str, top_k: int | None = None
    ) -> List[Dict]:
        """Search guidelines filtered by line of business."""
        if top_k is None:
            top_k = self._top_k
        if not self._table_exists():
            return []

        query_embedding = embed_query(query)
        db = self._get_db()
        table = db.open_table(self._table_name)

        results = (
            table.search(np.array(query_embedding, dtype=np.float32))
            .where(f'line_of_business = "{line_of_business}"')
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
                    "guideline_id": row["guideline_id"],
                    "line_of_business": row.get("line_of_business", ""),
                }
            )
        return output

    def list_guidelines(self) -> List[Dict]:
        """Return metadata for all stored guidelines."""
        self._rebuild_registry()
        return list(self._guideline_registry.values())

    def delete_guideline(self, guideline_id: str) -> bool:
        """Delete all chunks for a guideline."""
        if not self._table_exists():
            return False
        db = self._get_db()
        table = db.open_table(self._table_name)
        table.delete(f'guideline_id = "{guideline_id}"')
        self._guideline_registry.pop(guideline_id, None)
        return True


# ─── Singleton ────────────────────────────────────────────────────

_instance: GuidelinesStore | None = None


def get_guidelines_store() -> GuidelinesStore:
    """Return the singleton GuidelinesStore."""
    global _instance
    if _instance is None:
        _instance = GuidelinesStore()
    return _instance


def reset_guidelines_store() -> None:
    """Reset the singleton — used in tests."""
    global _instance
    _instance = None
