"""
RAG Retriever
=============
Performs vector similarity search against the ChromaDB knowledge base
to find relevant enterprise documents.

Phase 7: Will embed query and search ChromaDB for top-k results.
"""

from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions


def retrieve(query: str, top_k: int = 3) -> list:
    """
    Embed a query and retrieve the top-k most similar documents
    from the ChromaDB knowledge base collection.

    Args:
        query: The search query text
        top_k: Number of results to return (default: 3)

    Returns:
        List of dicts with source, snippet, and score
    """
    db_dir = Path(__file__).resolve().parent.parent / "database" / "chromadb"
    
    # Setup persistent ChromaDB client
    db_dir.parent.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(db_dir))
    
    # Check if collection exists. If not, build it dynamically.
    try:
        collections = [c.name for c in client.list_collections()]
    except Exception:
        collections = []
        
    if "knowledge_base" not in collections:
        print("[RAG Retriever] 'knowledge_base' collection not found. Initializing database dynamically...")
        from rag.loader import load_knowledge_base
        load_knowledge_base()
        
    try:
        # Initialize SentenceTransformer embedding function
        emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Get collection
        collection = client.get_collection(
            name="knowledge_base",
            embedding_function=emb_fn
        )
        
        # Query collection
        results = collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        # Format results to match the required schema
        formatted_results = []
        if results and "documents" in results and results["documents"]:
            documents = results["documents"][0]
            metadatas = results["metadatas"][0] if "metadatas" in results and results["metadatas"] else []
            distances = results["distances"][0] if "distances" in results and results["distances"] else []
            
            for i in range(len(documents)):
                snippet = documents[i]
                metadata = metadatas[i] if i < len(metadatas) else {}
                source = metadata.get("source", "unknown")
                
                # Convert distance to score (Chroma returns L2 distance by default, smaller is better)
                distance = distances[i] if i < len(distances) else 0.0
                score = 1.0 / (1.0 + distance)
                
                formatted_results.append({
                    "source": source,
                    "snippet": snippet,
                    "score": round(float(score), 4)
                })
                
        return formatted_results
        
    except Exception as e:
        print(f"[RAG Retriever] Error during retrieval: {e}")
        return []

