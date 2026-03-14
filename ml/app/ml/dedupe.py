from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("all-MiniLM-L6-v2")

stored_embeddings = []


def dedupe_check(text):
    """
    Detect duplicate resumes using embedding similarity
    """

    new_embedding = model.encode(text)

    for emb in stored_embeddings:

        similarity = cosine_similarity([new_embedding], [emb])[0][0]

        if similarity > 0.90:
            return {
                "duplicate": True,
                "similarity": float(similarity)
            }

    stored_embeddings.append(new_embedding)

    return {
        "duplicate": False
    }