from __future__ import annotations

import logging

from backend.llm.retry import with_retry
from backend.query.hybrid_router import HybridRouter
from backend.query.source_tracker import SourceTracker

logger = logging.getLogger(__name__)


class QueryEngine:
    """High-level query engine that combines hybrid routing with LlamaIndex querying.

    Parameters
    ----------
    index_manager:
        An :class:`~backend.indexing.index_manager.IndexManager` instance used
        to obtain the underlying LlamaIndex query engine.
    llm:
        The LLM instance (passed through for future use / context building).
    document_repo:
        A :class:`~backend.storage.document_repo.DocumentRepo` instance used to
        look up per-collection token counts.
    hybrid_router:
        Optional :class:`HybridRouter` instance. A default one is created when
        not supplied.
    """

    def __init__(
        self,
        index_manager,
        llm,
        document_repo,
        hybrid_router: HybridRouter | None = None,
    ) -> None:
        self._index_manager = index_manager
        self._llm = llm
        self._document_repo = document_repo
        self._router: HybridRouter = hybrid_router or HybridRouter()
        self._source_tracker = SourceTracker()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def query(self, question: str, collection_id: int | None = None) -> dict:
        """Execute a query and return an answer with source citations.

        Parameters
        ----------
        question:
            The user's natural language question.
        collection_id:
            When provided, the query is scoped to that collection.  The total
            token count for the collection is fetched from
            ``document_repo.total_tokens_for_collection`` and passed to the
            hybrid router to decide between full-context and RAG modes.

        Returns
        -------
        dict
            A dict with keys:
            ``answer`` (str), ``sources`` (list), ``sources_json`` (str),
            ``mode`` (str – "full_context" or "rag").
        """
        # 1. Determine routing mode via hybrid router
        collection_scoped = collection_id is not None
        if collection_scoped:
            total_tokens = self._document_repo.total_tokens_for_collection(collection_id)
        else:
            total_tokens = 0

        mode = self._router.decide(
            total_tokens=total_tokens,
            collection_scoped=collection_scoped,
        )
        logger.info(
            "Query routed to mode=%r (collection_id=%r, tokens=%d).",
            mode,
            collection_id,
            total_tokens,
        )

        # 2. Route to the appropriate query method
        if mode == "full_context":
            return self._query_full_context(question, collection_id)
        return self._query_rag(question, mode)

    # ------------------------------------------------------------------
    # Private query methods
    # ------------------------------------------------------------------

    def _query_rag(self, question: str, mode: str) -> dict:
        """Standard RAG query via the index."""
        engine = self._index_manager.get_query_engine()
        response = with_retry(lambda: engine.query(question))

        sources = self._source_tracker.extract(response)
        return {
            "answer": response.response,
            "sources": sources,
            "sources_json": self._source_tracker.to_json(sources),
            "mode": mode,
        }

    def _query_full_context(self, question: str, collection_id: int | None) -> dict:
        """Full-context mode: retrieve as much context as possible."""
        try:
            # Get a query engine with high top_k to approximate full context
            if self._index_manager._vector_index:
                engine = self._index_manager._vector_index.as_query_engine(
                    llm=self._index_manager._llm,
                    similarity_top_k=50,  # Retrieve many chunks for small collections
                )
            else:
                engine = self._index_manager.get_query_engine()

            response = with_retry(lambda: engine.query(question))

            sources = self._source_tracker.extract(response)
            return {
                "answer": response.response,
                "sources": sources,
                "sources_json": self._source_tracker.to_json(sources),
                "mode": "full_context",
            }
        except Exception:
            # fallback to normal RAG
            return self._query_rag(question, "full_context")
