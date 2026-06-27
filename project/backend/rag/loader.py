"""
RAG Loader
==========
Loads and indexes enterprise knowledge base documents into ChromaDB
for vector similarity search.

Phase 3: Placeholder - no real implementation yet.
Phase 7: Will chunk documents, embed with sentence-transformers,
         and store in persistent ChromaDB collection.
"""


def load_knowledge_base(path: str = "data/knowledge_base/") -> None:
    """
    Load all markdown files from the knowledge base directory,
    chunk them, embed with sentence-transformers, and store
    in a persistent ChromaDB collection.

    Args:
        path: Path to the knowledge base directory
    """
    # Phase 3: Placeholder
    print(f"[RAG Loader] Placeholder - will load KB from: {path}")
    pass
