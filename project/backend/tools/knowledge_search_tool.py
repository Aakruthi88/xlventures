"""
Knowledge Search Tool
=====================
LangChain tool to search the enterprise knowledge base (knowledge_memory collection in ChromaDB).
"""

from pathlib import Path
from typing import List, Dict, Any
from langchain.tools import tool
import chromadb
from chromadb.utils import embedding_functions

# Database path configuration
DB_DIR = Path(__file__).resolve().parents[2] / "database" / "chromadb"


@tool
def search_knowledge_base(query: str) -> List[Dict[str, Any]]:
    """
    Search the enterprise knowledge base (playbooks, compliance checklists, onboarding guides)
    for documents and procedures matching the given query text.

    Args:
        query: Semantic query text (e.g., 'SAP sync setup', 'renewal escalation matrix').

    Returns:
        List of matching document snippets containing: source filename, text snippet,
        and similarity score.
    """
    try:
        DB_DIR.parent.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(DB_DIR))

        # Check if collection exists
        try:
            collections = [c.name for c in client.list_collections()]
        except Exception:
            collections = []

        # If knowledge_memory is not present, load it dynamically using RAG loader (migrated)
        if "knowledge_memory" not in collections:
            print("[Knowledge Search Tool] 'knowledge_memory' collection missing. Building dynamically...")
            from rag.loader import load_knowledge_base
            load_knowledge_base()
            # Reinitialise client after build to pick up the new collection
            client = chromadb.PersistentClient(path=str(DB_DIR))

        emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        collection = client.get_collection(
            name="knowledge_memory",
            embedding_function=emb_fn
        )

        results = collection.query(
            query_texts=[query],
            n_results=3
        )

        formatted_results = []
        if results and "documents" in results and results["documents"]:
            documents = results["documents"][0]
            metadatas = results["metadatas"][0] if "metadatas" in results and results["metadatas"] else []
            distances = results["distances"][0] if "distances" in results and results["distances"] else []

            for i in range(len(documents)):
                snippet = documents[i]
                metadata = metadatas[i] if i < len(metadatas) else {}
                source = metadata.get("source", "unknown")
                distance = distances[i] if i < len(distances) else 0.0
                score = round(1.0 / (1.0 + distance), 4)

                formatted_results.append({
                    "source": source,
                    "snippet": snippet,
                    "score": score
                })

        return formatted_results

    except Exception as e:
        print(f"[Knowledge Search Tool] Error: {e}")
        return []
