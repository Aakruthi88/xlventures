"""
RAG Loader
==========
Loads and indexes enterprise knowledge base documents into ChromaDB
for vector similarity search.

Phase 7: Will chunk documents, embed with sentence-transformers,
         and store in persistent ChromaDB collection.
"""

import re
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions


def chunk_text_by_words(text: str, target_words: int = 220, overlap_words: int = 40) -> list:
    """
    Split markdown text into chunks of approximately target_words,
    ensuring sentences are not split in half.
    """
    # Split by sentences (simple regex checking for punctuation followed by space)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = []
    current_word_count = 0
    
    for sentence in sentences:
        sentence_words = sentence.split()
        if not sentence_words:
            continue
        
        # If adding this sentence exceeds target and we already have some text, save chunk
        if current_word_count + len(sentence_words) > target_words and current_chunk:
            chunks.append(" ".join(current_chunk))
            
            # Form overlap chunk by taking the last sentences that fit within overlap_words
            overlap_chunk = []
            overlap_count = 0
            for s in reversed(current_chunk):
                s_words = s.split()
                if overlap_count + len(s_words) <= overlap_words:
                    overlap_chunk.insert(0, s)
                    overlap_count += len(s_words)
                else:
                    break
            current_chunk = overlap_chunk
            current_word_count = overlap_count
        
        current_chunk.append(sentence)
        current_word_count += len(sentence_words)
        
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    return chunks


def load_knowledge_base(path: str = "data/knowledge_base/") -> None:
    """
    Load all markdown files from the knowledge base directory,
    chunk them, embed with sentence-transformers, and store
    in a persistent ChromaDB collection.

    Args:
        path: Path to the knowledge base directory
    """
    # Resolve absolute path to knowledge base directory
    kb_dir = Path(path)
    if not kb_dir.is_absolute():
        kb_dir = Path(__file__).resolve().parents[3] / kb_dir
        
    if not kb_dir.exists():
        print(f"[RAG Loader] Directory does not exist: {kb_dir}")
        return
        
    # Determine persistent database directory
    db_dir = Path(__file__).resolve().parent.parent / "database" / "chromadb"
    db_dir.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"[RAG Loader] Initializing persistent ChromaDB at: {db_dir}")
    client = chromadb.PersistentClient(path=str(db_dir))
    
    # Initialize SentenceTransformer embedding function
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    
    collection_name = "knowledge_base"
    
    # Recreate the collection to avoid duplicates or updates sync issues
    try:
        client.delete_collection(name=collection_name)
        print(f"[RAG Loader] Cleaned up existing collection: {collection_name}")
    except Exception:
        pass
        
    collection = client.create_collection(
        name=collection_name,
        embedding_function=emb_fn
    )
    
    documents = []
    metadatas = []
    ids = []
    
    chunk_counter = 0
    markdown_files = list(kb_dir.glob("*.md"))
    
    for file_path in markdown_files:
        filename = file_path.name
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Chunk the content (approx 220 words = ~300 tokens)
            chunks = chunk_text_by_words(content)
            
            for i, chunk in enumerate(chunks):
                documents.append(chunk)
                metadatas.append({"source": filename})
                ids.append(f"{filename}_chunk_{i}")
                chunk_counter += 1
                
        except Exception as e:
            print(f"[RAG Loader] Failed to load/chunk {filename}: {e}")
            
    if documents:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"[RAG Loader] Loaded {chunk_counter} chunks from {len(markdown_files)} files into collection '{collection_name}'")
    else:
        print("[RAG Loader] No documents found or parsed.")

