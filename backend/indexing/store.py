from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional dependency: chromadb
# ---------------------------------------------------------------------------
try:
    import chromadb
    _CHROMADB_AVAILABLE = True
except ImportError:  # pragma: no cover
    chromadb = None  # type: ignore[assignment]
    _CHROMADB_AVAILABLE = False
    logger.warning(
        "chromadb is not installed. ChromaStore will not function without it."
    )

# ---------------------------------------------------------------------------
# Optional dependency: llama_index ChromaVectorStore
# ---------------------------------------------------------------------------
try:
    from llama_index.vector_stores.chroma import ChromaVectorStore
    _CHROMA_VS_AVAILABLE = True
except ImportError:  # pragma: no cover
    ChromaVectorStore = None  # type: ignore[assignment,misc]
    _CHROMA_VS_AVAILABLE = False
    logger.warning(
        "llama_index.vector_stores.chroma is not installed. "
        "ChromaStore.get_vector_store will not function without it."
    )


class ChromaStore:
    """Thin management layer around a ChromaDB persistent client."""

    def __init__(self, persist_dir: str) -> None:
        if not _CHROMADB_AVAILABLE:
            raise RuntimeError(
                "chromadb is not installed. Install it with: pip install chromadb"
            )
        self._client = chromadb.PersistentClient(path=persist_dir)

    # ------------------------------------------------------------------
    # Collection helpers
    # ------------------------------------------------------------------

    def get_or_create_collection(self, name: str):
        """Get an existing collection or create it if it does not exist."""
        return self._client.get_or_create_collection(name=name)

    def get_vector_store(self, collection_name: str):
        """Return a LlamaIndex ChromaVectorStore for the given collection."""
        if not _CHROMA_VS_AVAILABLE:
            raise RuntimeError(
                "llama_index.vector_stores.chroma is not installed. "
                "Install it with: pip install llama-index-vector-stores-chroma"
            )
        chroma_collection = self.get_or_create_collection(collection_name)
        return ChromaVectorStore(chroma_collection=chroma_collection)

    def delete_documents_by_source(self, collection_name: str, source_path: str) -> int:
        """Delete all vectors in a collection whose metadata 'source' matches source_path.

        Returns the number of deleted entries (0 if none found or collection missing).
        """
        try:
            coll = self._client.get_or_create_collection(name=collection_name)
            # Query for matching documents
            results = coll.get(where={"source": source_path})
            if results and results["ids"]:
                coll.delete(ids=results["ids"])
                logger.info(
                    "Deleted %d vectors for source=%s from collection=%s",
                    len(results["ids"]),
                    source_path,
                    collection_name,
                )
                return len(results["ids"])
            return 0
        except Exception as exc:
            logger.warning("Failed to delete vectors for source %s: %s", source_path, exc)
            return 0

    def delete_collection(self, name: str) -> None:
        """Delete a collection by name, logging a warning on failure."""
        try:
            self._client.delete_collection(name=name)
        except Exception as e:
            logger.warning(f"Failed to delete collection {name}: {e}")

    def list_collections(self):
        """Return a list of all collections managed by this client."""
        return self._client.list_collections()
