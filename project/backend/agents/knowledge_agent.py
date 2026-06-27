"""
Knowledge Agent
===============
Retrieves relevant enterprise knowledge documents using RAG
(Retrieval-Augmented Generation) from the knowledge base.

Phase 7: Uses ChromaDB + sentence-transformers for real retrieval.
"""

from rag.retriever import retrieve as rag_retrieve


def retrieve(transcript_text: str) -> dict:
    """
    Retrieve relevant knowledge base documents for a given transcript.

    Args:
        transcript_text: The customer meeting transcript text

    Returns:
        dict matching KnowledgeAgent schema with retrieved_docs
    """
    docs = rag_retrieve(transcript_text, top_k=3)
    return {
        "retrieved_docs": docs
    }

