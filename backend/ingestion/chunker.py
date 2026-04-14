from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional LlamaIndex imports – each wrapped in try/except so missing
# libraries don't crash at import time.  Module-level names allow tests to
# patch them easily.
# ---------------------------------------------------------------------------

try:
    from llama_index.core.node_parser import HierarchicalNodeParser, SentenceSplitter
except Exception:  # ImportError or any install-time error
    HierarchicalNodeParser = None  # type: ignore[assignment,misc]
    SentenceSplitter = None  # type: ignore[assignment,misc]

try:
    from llama_index.core.node_parser import SemanticSplitterNodeParser
except Exception:
    SemanticSplitterNodeParser = None  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# Chunker
# ---------------------------------------------------------------------------

class Chunker:
    """Branch between Hierarchical and Semantic chunking strategies.

    Parameters
    ----------
    chunk_sizes:
        Hierarchy sizes passed to ``HierarchicalNodeParser``.
        Defaults to ``[1024, 512, 256]`` (large / medium / small).
    """

    def __init__(self, chunk_sizes: list[int] | None = None) -> None:
        self._chunk_sizes: list[int] = chunk_sizes or [1024, 512, 256]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chunk(
        self,
        documents: list,
        has_structure: bool,
        embed_model=None,
    ) -> list:
        """Chunk *documents* using the appropriate strategy.

        Parameters
        ----------
        documents:
            List of document objects (e.g. LlamaIndex ``Document`` instances).
        has_structure:
            ``True`` for structured documents (PDFs with headings, Markdown).
            ``False`` for unstructured documents (plain text, transcripts).
        embed_model:
            Optional embedding model passed to ``SemanticSplitterNodeParser``.
            When ``None`` and ``has_structure`` is ``False``, falls back to
            ``SentenceSplitter``.

        Returns
        -------
        list
            List of parsed nodes.  Empty list when *documents* is empty.
        """
        if not documents:
            return []

        if has_structure:
            return self._hierarchical_chunk(documents)
        else:
            return self._semantic_chunk(documents, embed_model)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _hierarchical_chunk(self, documents: list) -> list:
        """For structured documents (PDFs with headings, Markdown).

        Uses ``HierarchicalNodeParser`` with the configured ``chunk_sizes``
        to create a large/medium/small node hierarchy.
        """
        parser = HierarchicalNodeParser.from_defaults(chunk_sizes=self._chunk_sizes)
        nodes = parser.get_nodes_from_documents(documents)
        logger.info(
            "Hierarchical chunking produced %d nodes (chunk_sizes=%s)",
            len(nodes),
            self._chunk_sizes,
        )
        return nodes

    def _semantic_chunk(self, documents: list, embed_model=None) -> list:
        """For unstructured documents (plain text, YouTube transcripts).

        Tries ``SemanticSplitterNodeParser`` when an *embed_model* is provided.
        Falls back to ``SentenceSplitter(chunk_size=512, chunk_overlap=50)``
        when:

        * no *embed_model* is given, or
        * ``SemanticSplitterNodeParser`` is unavailable, or
        * ``SemanticSplitterNodeParser`` raises during parsing.
        """
        if embed_model is not None:
            try:
                parser = SemanticSplitterNodeParser(embed_model=embed_model)
                nodes = parser.get_nodes_from_documents(documents)
                logger.info(
                    "Semantic chunking produced %d nodes", len(nodes)
                )
                return nodes
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "SemanticSplitterNodeParser failed (%s); "
                    "falling back to SentenceSplitter.",
                    exc,
                )

        # Fallback: SentenceSplitter
        parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)
        nodes = parser.get_nodes_from_documents(documents)
        logger.info(
            "SentenceSplitter fallback produced %d nodes", len(nodes)
        )
        return nodes
