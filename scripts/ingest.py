"""Ingest destination markdown files into ChromaDB vector store."""
import os
import sys

# Allow running from project root: python scripts/ingest.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import config

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "destinations")
_COLLECTION_NAME = "travel_knowledge"
_CHUNK_SIZE = 500
_CHUNK_OVERLAP = 50


def _chunk_text(text: str) -> list[str]:
    """Split text into overlapping chunks by character count."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + _CHUNK_SIZE
        chunks.append(text[start:end].strip())
        start += _CHUNK_SIZE - _CHUNK_OVERLAP
    return [c for c in chunks if c]


def _load_documents(data_dir: str) -> list[dict]:
    """Load all .md files from data directory."""
    docs = []
    for filename in os.listdir(data_dir):
        if not filename.endswith(".md"):
            continue
        filepath = os.path.join(data_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        docs.append({"content": content, "source_file": filename})
    return docs


def ingest(data_dir: str = _DATA_DIR, reset: bool = False) -> int:
    """
    Load markdown files, chunk, embed, and upsert into ChromaDB.
    Returns total number of chunks inserted.
    """
    import chromadb
    from chromadb.utils import embedding_functions

    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=config.EMBEDDING_MODEL
    )
    client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)

    if reset:
        try:
            client.delete_collection(_COLLECTION_NAME)
            print(f"[ingest] Deleted existing collection '{_COLLECTION_NAME}'")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=_COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    docs = _load_documents(data_dir)
    if not docs:
        print(f"[ingest] No .md files found in {data_dir}")
        return 0

    all_ids = []
    all_documents = []
    all_metadatas = []

    for doc in docs:
        chunks = _chunk_text(doc["content"])
        base_name = doc["source_file"].replace(".md", "")
        for i, chunk in enumerate(chunks):
            chunk_id = f"{base_name}_{i:04d}"
            all_ids.append(chunk_id)
            all_documents.append(chunk)
            all_metadatas.append({"source_file": doc["source_file"], "chunk_index": i})

    # Upsert in batches of 100
    batch_size = 100
    for start in range(0, len(all_ids), batch_size):
        collection.upsert(
            ids=all_ids[start : start + batch_size],
            documents=all_documents[start : start + batch_size],
            metadatas=all_metadatas[start : start + batch_size],
        )

    total = len(all_ids)
    print(f"[ingest] Upserted {total} chunks from {len(docs)} files into '{_COLLECTION_NAME}'")
    return total


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingest travel knowledge into ChromaDB")
    parser.add_argument("--reset", action="store_true", help="Delete and recreate collection before ingesting")
    parser.add_argument("--data-dir", default=_DATA_DIR, help="Directory containing .md destination files")
    args = parser.parse_args()

    ingest(data_dir=args.data_dir, reset=args.reset)
