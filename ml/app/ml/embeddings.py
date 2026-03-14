from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import os

model = SentenceTransformer("all-MiniLM-L6-v2")

# Initialize ChromaDB client
chroma_path = os.getenv("CHROMA_PATH", "./chroma_db")
client = chromadb.PersistentClient(path=chroma_path)

# Get or create collection
collection = client.get_or_create_collection("candidates_vectors")


def create_embedding(text):
    """Generate embedding for text"""
    return model.encode(text).tolist()


def store_embedding(candidate_id, text):
    """Store candidate embedding in ChromaDB"""
    embedding = create_embedding(text)
    
    collection.upsert(
        documents=[text],
        embeddings=[embedding],
        ids=[str(candidate_id)]
    )


def semantic_search(query, n_results=10):
    """
    Search for similar candidates using semantic search.
    
    Returns candidate IDs and similarity scores. The backend will
    enrich these results with full candidate data from PostgreSQL.
    """
    query_embedding = create_embedding(query)
    
    try:
        # Query ChromaDB with more results to allow filtering
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results * 2, 50)  # Get more results for filtering
        )
        
        candidates = []
        
        if results.get("ids") and len(results["ids"]) > 0:
            ids = results["ids"][0]
            distances = results.get("distances", [[]])[0]
            
            for i, candidate_id in enumerate(ids):
                distance = distances[i] if i < len(distances) else float('inf')
                
                # Filter out weak matches (distance > 1.6)
                if distance > 1.6:
                    continue
                
                # Convert distance to similarity score: similarity = 1 / (1 + distance)
                # This ensures: distance=0 -> similarity=1.0, distance=1.6 -> similarity=0.38
                similarity_score = 1.0 / (1.0 + distance)
                
                candidates.append({
                    "id": candidate_id,
                    "similarity_score": round(similarity_score, 4)
                })
        
        # Sort by similarity score descending (higher = better)
        candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        # Limit to requested number of results
        candidates = candidates[:n_results]
        
        return {
            "query": query,
            "total_results": len(candidates),
            "candidates": candidates
        }
    
    except Exception as e:
        return {
            "query": query,
            "total_results": 0,
            "candidates": [],
            "error": str(e)
        }


def show_embeddings():
    """Get all stored embeddings"""
    data = collection.get(include=["documents", "embeddings", "metadatas"])
    
    # Convert numpy arrays to lists if needed
    if data.get("embeddings") is not None and len(data.get("embeddings", [])) > 0:
        embeddings_list = []
        for emb in data["embeddings"]:
            if isinstance(emb, list):
                embeddings_list.append(emb)
            else:
                # Handle numpy array or other types
                try:
                    embeddings_list.append(emb.tolist())
                except:
                    embeddings_list.append(list(emb))
        data["embeddings"] = embeddings_list
    
    return data