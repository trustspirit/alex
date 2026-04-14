from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional LlamaIndex imports – each wrapped in try/except so missing
# libraries don't crash at import time.  Module-level names allow tests to
# patch them easily.
# ---------------------------------------------------------------------------

try:
    from llama_index.core import VectorStoreIndex, DocumentSummaryIndex, StorageContext, Document
except Exception:
    VectorStoreIndex = None  # type: ignore[assignment,misc]
    DocumentSummaryIndex = None  # type: ignore[assignment,misc]
    StorageContext = None  # type: ignore[assignment,misc]
    Document = None  # type: ignore[assignment,misc]

try:
    from llama_index.core.query_engine import RouterQueryEngine
except Exception:
    RouterQueryEngine = None  # type: ignore[assignment,misc]

try:
    from llama_index.core.selectors import LLMSingleSelector
except Exception:
    LLMSingleSelector = None  # type: ignore[assignment,misc]

try:
    from llama_index.core.tools import QueryEngineTool
except Exception:
    QueryEngineTool = None  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# IndexManager
# ---------------------------------------------------------------------------

class IndexManager:
    """Build, load, and compose LlamaIndex indexes for RAG queries.

    Parameters
    ----------
    vector_store:
        A LlamaIndex-compatible vector store (e.g. ChromaVectorStore).
    embed_model:
        The embedding model used when building/loading indexes.
    llm:
        Optional LLM used by DocumentSummaryIndex and LLMSingleSelector.
    """

    def __init__(self, vector_store, embed_model, llm=None) -> None:
        self._vector_store = vector_store
        self._embed_model = embed_model
        self._llm = llm
        self._vector_index = None
        self._summary_index = None

    # ------------------------------------------------------------------
    # Index builders
    # ------------------------------------------------------------------

    def build_vector_index(self, nodes) -> object:
        """Build a VectorStoreIndex from *nodes* using the configured vector store.

        Returns
        -------
        object
            The constructed ``VectorStoreIndex`` instance.
        """
        logger.info("Building VectorStoreIndex from %d nodes.", len(nodes))
        storage_context = StorageContext.from_defaults(vector_store=self._vector_store)
        index = VectorStoreIndex(
            nodes=nodes,
            storage_context=storage_context,
            embed_model=self._embed_model,
        )
        self._vector_index = index
        logger.info("VectorStoreIndex built successfully.")
        return index

    def build_summary_index(self, nodes) -> object:
        """Build a DocumentSummaryIndex from *nodes*.

        Nodes are converted to ``Document`` objects before indexing so that
        ``DocumentSummaryIndex.from_documents`` can process them.

        Returns
        -------
        object
            The constructed ``DocumentSummaryIndex`` instance.
        """
        logger.info("Building DocumentSummaryIndex from %d nodes.", len(nodes))
        docs = [Document(text=node.text) for node in nodes]
        index = DocumentSummaryIndex.from_documents(
            docs,
            llm=self._llm,
            embed_model=self._embed_model,
        )
        self._summary_index = index
        logger.info("DocumentSummaryIndex built successfully.")
        return index

    # ------------------------------------------------------------------
    # Index loaders
    # ------------------------------------------------------------------

    def load_existing_vector_index(self) -> object:
        """Load an existing VectorStoreIndex directly from the configured ChromaDB store.

        Returns
        -------
        object
            The loaded ``VectorStoreIndex`` instance.
        """
        logger.info("Loading existing VectorStoreIndex from vector store.")
        index = VectorStoreIndex.from_vector_store(self._vector_store)
        self._vector_index = index
        logger.info("Existing VectorStoreIndex loaded successfully.")
        return index

    # ------------------------------------------------------------------
    # Query engine composition
    # ------------------------------------------------------------------

    def get_query_engine(self) -> object:
        """Create a query engine from the available indexes.

        - If no index is available, raises ``RuntimeError``.
        - If only one index is available, returns its query engine directly.
        - If both indexes are available, composes them via
          ``RouterQueryEngine`` with ``LLMSingleSelector``.

        Returns
        -------
        object
            A query engine ready to answer questions.

        Raises
        ------
        RuntimeError
            When no indexes have been built or loaded.
        """
        available_indexes: list = []

        if self._vector_index is not None:
            available_indexes.append(("vector", self._vector_index))

        if self._summary_index is not None:
            available_indexes.append(("summary", self._summary_index))

        if not available_indexes:
            raise RuntimeError(
                "No indexes available. Please ingest documents first."
            )

        if len(available_indexes) == 1:
            # Only one index – return its query engine directly; no router needed.
            kind, index = available_indexes[0]
            logger.info(
                "Single index available (%s); returning its query engine directly.",
                kind,
            )
            return index.as_query_engine(
                embed_model=self._embed_model,
                llm=self._llm,
            )

        # Two indexes: build QueryEngineTool wrappers and compose via RouterQueryEngine
        logger.info(
            "Multiple indexes available (%d); composing with RouterQueryEngine.",
            len(available_indexes),
        )
        tools: list = []

        vector_qe = self._vector_index.as_query_engine(
            embed_model=self._embed_model,
            llm=self._llm,
        )
        tools.append(
            QueryEngineTool(
                query_engine=vector_qe,
                description=(
                    "Useful for finding specific facts, details, or passages "
                    "from documents based on semantic similarity."
                ),
            )
        )

        summary_qe = self._summary_index.as_query_engine(
            embed_model=self._embed_model,
            llm=self._llm,
        )
        tools.append(
            QueryEngineTool(
                query_engine=summary_qe,
                description=(
                    "Useful for summarization questions, getting an overview "
                    "of a document, or understanding what a document is about."
                ),
            )
        )

        selector = LLMSingleSelector.from_defaults(llm=self._llm)
        return RouterQueryEngine.from_defaults(
            selector=selector,
            query_engine_tools=tools,
        )
