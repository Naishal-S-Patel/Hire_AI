"""
Embeddings module — sentence-transformers encoding + ChromaDB storage / retrieval.
"""

from __future__ import annotations

import uuid
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer

from app.config import settings

# ── Lazy singletons ───────────────────────────────────────
_model: SentenceTransformer | None = None
_chroma_client: chromadb.ClientAPI | None = None
_collection = None

MODEL_NAME = "all-MiniLM-L6-v2"
COLLECTION_NAME = "candidate_embeddings"


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def _get_collection():
    global _chroma_client, _collection
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
    if _collection is None:
        _collection = _chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def encode_text(text: str) -> list[float]:
    """Encode a single text string into a dense vector."""
    model = _get_model()
    return model.encode(text, normalize_embeddings=True).tolist()


def encode_texts(texts: list[str]) -> list[list[float]]:
    """Encode a batch of texts into dense vectors."""
    model = _get_model()
    return model.encode(texts, normalize_embeddings=True).tolist()


def upsert_embedding(
    candidate_id: str,
    text: str,
    metadata: dict[str, Any] | None = None,
) -> str:
    """
    Encode text, upsert into ChromaDB, return the chroma doc ID.
    """
    collection = _get_collection()
    vector = encode_text(text)
    chroma_id = f"cand-{candidate_id}"
    meta = {"candidate_id": candidate_id, **(metadata or {})}
    collection.upsert(
        ids=[chroma_id],
        embeddings=[vector],
        documents=[text],
        metadatas=[meta],
    )
    return chroma_id


def query_similar(query_text: str, top_k: int = 10, where: dict | None = None) -> list[dict[str, Any]]:
    """
    Query ChromaDB for candidates similar to query_text.

    Returns list of dicts with candidate_id, score, document.
    """
    collection = _get_collection()
    vector = encode_text(query_text)
    kwargs: dict[str, Any] = {
        "query_embeddings": [vector],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        kwargs["where"] = where
    results = collection.query(**kwargs)
    output: list[dict[str, Any]] = []
    ids = results.get("ids", [[]])[0]
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    for i, doc_id in enumerate(ids):
        output.append({
            "chroma_id": doc_id,
            "candidate_id": metas[i].get("candidate_id") if metas[i] else None,
            "score": 1 - distances[i],  # cosine distance → similarity
            "document": docs[i] if docs else None,
        })
    return output


def delete_embedding(candidate_id: str) -> None:
    """Remove a candidate's embedding from ChromaDB."""
    collection = _get_collection()
    chroma_id = f"cand-{candidate_id}"
    try:
        collection.delete(ids=[chroma_id])
    except Exception:
        pass
