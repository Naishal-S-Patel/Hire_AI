"""
Deduplication engine — finds and merges duplicate candidates via cosine similarity.
"""

from __future__ import annotations

from typing import Any

from app.ml.embeddings.embedder import _get_collection, encode_text


def find_duplicates(candidate_id: str, threshold: float = 0.85) -> list[dict[str, Any]]:
    """
    Find candidates similar to the given candidate above the similarity threshold.

    Returns a list of potential duplicates with similarity scores.
    """
    collection = _get_collection()
    chroma_id = f"cand-{candidate_id}"

    # Get the candidate's embedding document
    try:
        existing = collection.get(ids=[chroma_id], include=["documents", "embeddings"])
    except Exception:
        return []

    if not existing["documents"]:
        return []

    doc_text = existing["documents"][0]
    vector = encode_text(doc_text)

    results = collection.query(
        query_embeddings=[vector],
        n_results=20,
        include=["documents", "metadatas", "distances"],
    )

    duplicates: list[dict[str, Any]] = []
    ids = results.get("ids", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for i, doc_id in enumerate(ids):
        if doc_id == chroma_id:
            continue  # skip self
        similarity = 1 - distances[i]
        if similarity >= threshold:
            duplicates.append({
                "chroma_id": doc_id,
                "candidate_id": metas[i].get("candidate_id") if metas[i] else None,
                "similarity": round(similarity, 4),
            })

    return duplicates


def scan_all_duplicates(threshold: float = 0.85) -> list[dict[str, Any]]:
    """
    Scan the entire collection for duplicate pairs.

    Returns list of duplicate groups.
    """
    collection = _get_collection()
    all_data = collection.get(include=["metadatas", "embeddings", "documents"])

    if not all_data["ids"]:
        return []

    seen_pairs: set[tuple[str, str]] = set()
    duplicate_groups: list[dict[str, Any]] = []

    for i, cand_id in enumerate(all_data["ids"]):
        results = collection.query(
            query_embeddings=[all_data["embeddings"][i]],
            n_results=10,
            include=["metadatas", "distances"],
        )
        matches = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]
        metas = results.get("metadatas", [[]])[0]

        for j, match_id in enumerate(matches):
            if match_id == cand_id:
                continue
            pair = tuple(sorted([cand_id, match_id]))
            if pair in seen_pairs:
                continue
            similarity = 1 - distances[j]
            if similarity >= threshold:
                seen_pairs.add(pair)
                duplicate_groups.append({
                    "candidate_a": cand_id,
                    "candidate_b": match_id,
                    "similarity": round(similarity, 4),
                })

    return duplicate_groups
