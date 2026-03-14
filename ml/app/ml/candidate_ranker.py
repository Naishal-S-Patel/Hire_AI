from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import chromadb
import os

model = SentenceTransformer("all-MiniLM-L6-v2")

# Initialize ChromaDB client
chroma_path = os.getenv("CHROMA_PATH", "./chroma_db")
client = chromadb.PersistentClient(path=chroma_path)

collection = client.get_or_create_collection("resume_embeddings")


def rank_candidates(job_description):
    """Rank candidates based on job description similarity"""
    job_embedding = model.encode(job_description).tolist()

    data = collection.get(include=["embeddings", "documents"])

    if not data["ids"] or len(data["ids"]) == 0:
        return []

    scores = []

    for i, emb in enumerate(data["embeddings"]):
        similarity = cosine_similarity([job_embedding], [emb])[0][0]

        scores.append({
            "candidate_id": data["ids"][i],
            "resume": data["documents"][i][:200],  # Truncate for response
            "score": float(similarity)
        })

    ranked = sorted(scores, key=lambda x: x["score"], reverse=True)

    return ranked[:5]