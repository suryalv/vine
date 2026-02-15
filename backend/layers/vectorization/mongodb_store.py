from __future__ import annotations

"""
VECTORIZATION LAYER — MongoDB Atlas Backend
=============================================
MongoDB Atlas Vector Search for document chunk embeddings.
Uses pymongo with $vectorSearch aggregation pipeline.

To use: pip install pymongo
Set config: VECTOR_STORE_BACKEND=mongodb_atlas
            MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net
            MONGODB_DATABASE=uw_companion
            MONGODB_COLLECTION=document_chunks

Requires an Atlas Vector Search index named "vector_index" on the
collection's "embedding" field.

Team Owner: Data Infrastructure Team
"""

from typing import List, Dict

import numpy as np

from config import MONGODB_URI, MONGODB_DATABASE, MONGODB_COLLECTION, TOP_K_RESULTS
from layers.embedding import embed_texts, embed_query
from layers.vectorization.base import VectorStore


class MongoDBAtlasStore(VectorStore):
    """MongoDB Atlas Vector Search backed vector store."""

    def __init__(
        self,
        uri: str = MONGODB_URI,
        database: str = MONGODB_DATABASE,
        collection: str = MONGODB_COLLECTION,
        top_k: int = TOP_K_RESULTS,
        index_name: str = "vector_index",
    ):
        self._uri = uri
        self._database_name = database
        self._collection_name = collection
        self._top_k = top_k
        self._index_name = index_name
        self._client = None
        self._db = None
        self._collection = None

    def _get_collection(self):
        if self._client is None:
            from pymongo import MongoClient

            self._client = MongoClient(self._uri)
            self._db = self._client[self._database_name]
            self._collection = self._db[self._collection_name]
            self._collection.create_index("document_id")
            self._collection.create_index("chunk_id", unique=True)
        return self._collection

    def store_chunks(
        self, chunks: List[Dict], document_id: str, filename: str, num_pages: int
    ) -> int:
        if not chunks:
            return 0

        texts = [c["text"] for c in chunks]
        embeddings = embed_texts(texts)

        collection = self._get_collection()
        documents = []
        for chunk, embedding in zip(chunks, embeddings):
            documents.append(
                {
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"],
                    "source": chunk["source"],
                    "page": chunk["page"],
                    "section": chunk.get("section", ""),
                    "document_id": document_id,
                    "embedding": np.array(embedding, dtype=np.float32).tolist(),
                }
            )
        collection.insert_many(documents)

        # Store/update document metadata
        meta = self._db["document_metadata"]
        meta.update_one(
            {"document_id": document_id},
            {
                "$set": {
                    "document_id": document_id,
                    "filename": filename,
                    "num_chunks": len(chunks),
                    "num_pages": num_pages,
                }
            },
            upsert=True,
        )
        return len(documents)

    def search(self, query: str, top_k: int = None) -> List[Dict]:
        if top_k is None:
            top_k = self._top_k

        query_embedding = embed_query(query)
        collection = self._get_collection()

        pipeline = [
            {
                "$vectorSearch": {
                    "index": self._index_name,
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": top_k * 10,
                    "limit": top_k,
                }
            },
            {
                "$addFields": {
                    "similarity": {"$meta": "vectorSearchScore"},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "text": 1,
                    "source": 1,
                    "page": 1,
                    "section": 1,
                    "document_id": 1,
                    "similarity": 1,
                }
            },
        ]
        results = list(collection.aggregate(pipeline))
        return [
            {
                "text": r["text"],
                "source": r["source"],
                "page": r["page"],
                "section": r.get("section", ""),
                "similarity": float(r.get("similarity", 0)),
                "document_id": r["document_id"],
            }
            for r in results
        ]

    def get_all_documents(self) -> List[Dict]:
        meta = self._db["document_metadata"]
        return [
            {
                "document_id": d["document_id"],
                "filename": d["filename"],
                "num_chunks": d["num_chunks"],
                "num_pages": d["num_pages"],
            }
            for d in meta.find({}, {"_id": 0})
        ]

    def delete_document(self, document_id: str) -> bool:
        collection = self._get_collection()
        result = collection.delete_many({"document_id": document_id})
        meta = self._db["document_metadata"]
        meta.delete_one({"document_id": document_id})
        return result.deleted_count > 0

    def get_chunks_by_document(self, document_id: str) -> List[Dict]:
        collection = self._get_collection()
        cursor = collection.find(
            {"document_id": document_id},
            {"_id": 0, "text": 1, "source": 1, "page": 1, "embedding": 1},
        ).limit(1000)
        return [
            {
                "text": r["text"],
                "source": r["source"],
                "page": r["page"],
                "vector": r.get("embedding"),
            }
            for r in cursor
        ]
