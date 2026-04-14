from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class HybridRouter:
    """Decides whether to use full-context or RAG mode for a query.

    Parameters
    ----------
    threshold_tokens:
        Maximum number of tokens for which full-context mode is used when the
        query is collection-scoped. Queries whose total token count exceeds
        this threshold are routed to RAG mode. Defaults to 8000.
    """

    def __init__(self, threshold_tokens: int = 8000) -> None:
        self._threshold = threshold_tokens

    def decide(self, total_tokens: int, collection_scoped: bool) -> str:
        """Return "full_context" or "rag" depending on query context.

        Parameters
        ----------
        total_tokens:
            Total token count for the documents in scope.
        collection_scoped:
            ``True`` if the query is restricted to a specific collection,
            ``False`` for unscoped (global) queries.

        Returns
        -------
        str
            ``"full_context"`` when the collection is small enough to pass
            entirely to the LLM context window, ``"rag"`` otherwise.
        """
        if not collection_scoped:
            logger.debug("Query is unscoped – routing to RAG.")
            return "rag"
        if total_tokens <= self._threshold:
            logger.debug(
                "Token count %d <= threshold %d – routing to full_context.",
                total_tokens,
                self._threshold,
            )
            return "full_context"
        logger.debug(
            "Token count %d > threshold %d – routing to RAG.",
            total_tokens,
            self._threshold,
        )
        return "rag"
