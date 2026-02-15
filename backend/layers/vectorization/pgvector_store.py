from __future__ import annotations

"""
VECTORIZATION LAYER — PgVector Backend
=======================================
PostgreSQL + pgvector extension for document chunk embeddings.
Uses psycopg2 for synchronous connections.

To use: pip install psycopg2-binary
Set config: VECTOR_STORE_BACKEND=pgvector
            PGVECTOR_CONNECTION_STRING=postgresql://user:pass@host:5432/db

Team Owner: Data Infrastructure Team
"""

from typing import List, Dict

import numpy as np

from config import PGVECTOR_CONNECTION_STRING, EMBEDDING_DIM, TOP_K_RESULTS
from layers.embedding import embed_texts, embed_query
from layers.vectorization.base import VectorStore


class PgVectorStore(VectorStore):
    """PostgreSQL + pgvector backed vector store."""

    def __init__(
        self,
        connection_string: str = PGVECTOR_CONNECTION_STRING,
        embedding_dim: int = EMBEDDING_DIM,
        top_k: int = TOP_K_RESULTS,
        table_name: str = "document_chunks",
    ):
        self._connection_string = connection_string
        self._embedding_dim = embedding_dim
        self._top_k = top_k
        self._table_name = table_name
        self._conn = None
        self._initialized = False

    def _get_conn(self):
        if self._conn is None or self._conn.closed:
            import psycopg2

            self._conn = psycopg2.connect(self._connection_string)
            self._conn.autocommit = False
        if not self._initialized:
            self._ensure_tables()
            self._initialized = True
        return self._conn

    def _ensure_tables(self):
        """Create the chunks and metadata tables if they don't exist."""
        conn = self._conn
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {self._table_name} (
                    id SERIAL PRIMARY KEY,
                    chunk_id TEXT NOT NULL,
                    text TEXT NOT NULL,
                    source TEXT NOT NULL,
                    page INTEGER NOT NULL,
                    section TEXT DEFAULT '',
                    document_id TEXT NOT NULL,
                    embedding vector({self._embedding_dim})
                )
            """)
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{self._table_name}_doc_id
                ON {self._table_name} (document_id)
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS document_metadata (
                    document_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    num_chunks INTEGER NOT NULL,
                    num_pages INTEGER NOT NULL
                )
            """)
        conn.commit()

    def store_chunks(
        self, chunks: List[Dict], document_id: str, filename: str, num_pages: int
    ) -> int:
        if not chunks:
            return 0

        texts = [c["text"] for c in chunks]
        embeddings = embed_texts(texts)

        conn = self._get_conn()
        with conn.cursor() as cur:
            for chunk, embedding in zip(chunks, embeddings):
                vec_list = np.array(embedding, dtype=np.float32).tolist()
                cur.execute(
                    f"""
                    INSERT INTO {self._table_name}
                        (chunk_id, text, source, page, section, document_id, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        chunk["chunk_id"],
                        chunk["text"],
                        chunk["source"],
                        chunk["page"],
                        chunk.get("section", ""),
                        document_id,
                        str(vec_list),
                    ),
                )
            cur.execute(
                """
                INSERT INTO document_metadata (document_id, filename, num_chunks, num_pages)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (document_id) DO UPDATE SET
                    filename = EXCLUDED.filename,
                    num_chunks = EXCLUDED.num_chunks,
                    num_pages = EXCLUDED.num_pages
                """,
                (document_id, filename, len(chunks), num_pages),
            )
        conn.commit()
        return len(chunks)

    def search(self, query: str, top_k: int = None) -> List[Dict]:
        if top_k is None:
            top_k = self._top_k

        query_embedding = embed_query(query)
        vec_str = str(np.array(query_embedding, dtype=np.float32).tolist())

        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT text, source, page, section, document_id,
                       1 - (embedding <=> %s::vector) AS similarity
                FROM {self._table_name}
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (vec_str, vec_str, top_k),
            )
            rows = cur.fetchall()

        return [
            {
                "text": row[0],
                "source": row[1],
                "page": row[2],
                "section": row[3] or "",
                "similarity": float(row[5]),
                "document_id": row[4],
            }
            for row in rows
        ]

    def get_all_documents(self) -> List[Dict]:
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT document_id, filename, num_chunks, num_pages FROM document_metadata"
            )
            rows = cur.fetchall()
        return [
            {
                "document_id": row[0],
                "filename": row[1],
                "num_chunks": row[2],
                "num_pages": row[3],
            }
            for row in rows
        ]

    def delete_document(self, document_id: str) -> bool:
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {self._table_name} WHERE document_id = %s",
                (document_id,),
            )
            deleted = cur.rowcount > 0
            cur.execute(
                "DELETE FROM document_metadata WHERE document_id = %s",
                (document_id,),
            )
        conn.commit()
        return deleted

    def get_chunks_by_document(self, document_id: str) -> List[Dict]:
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT text, source, page, embedding
                FROM {self._table_name}
                WHERE document_id = %s
                LIMIT 1000
                """,
                (document_id,),
            )
            rows = cur.fetchall()
        return [
            {"text": row[0], "source": row[1], "page": row[2], "vector": row[3]}
            for row in rows
        ]
