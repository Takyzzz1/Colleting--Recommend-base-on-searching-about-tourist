"""RAG retrieval tool using ChromaDB and local HuggingFace embeddings."""
from langchain_core.tools import tool
from app.config import config


def _get_collection():
    import chromadb
    from chromadb.utils import embedding_functions

    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=config.EMBEDDING_MODEL
    )
    client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)
    try:
        return client.get_collection(name="travel_knowledge", embedding_function=ef)
    except Exception:
        return None


@tool
def rag_search(query: str, n_results: int = 3) -> dict:
    """Search the local travel knowledge base for destination information."""
    collection = _get_collection()

    if collection is None or collection.count() == 0:
        return {"context": "", "sources": []}

    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas"],
    )

    documents = results["documents"][0] if results["documents"] else []
    metadatas = results["metadatas"][0] if results["metadatas"] else []

    if not documents:
        return {"context": "", "sources": []}

    context = "\n\n---\n\n".join(documents)
    sources = list({m.get("source_file", "") for m in metadatas if m.get("source_file")})

    return {"context": context, "sources": sources}
