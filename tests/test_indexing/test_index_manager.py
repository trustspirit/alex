from __future__ import annotations

from unittest.mock import MagicMock, patch, call

import pytest

from backend.indexing.index_manager import IndexManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_node(text: str = "Test content", id_: str = "1") -> MagicMock:
    """Return a mock node with .text and .id_ attributes."""
    node = MagicMock()
    node.text = text
    node.id_ = id_
    return node


# ---------------------------------------------------------------------------
# test_build_vector_index
# ---------------------------------------------------------------------------

def test_build_vector_index():
    """build_vector_index creates a VectorStoreIndex using StorageContext."""
    mock_vector_store = MagicMock()
    mock_embed_model = MagicMock()
    nodes = [_make_node("Test content", "1")]

    with patch("backend.indexing.index_manager.VectorStoreIndex") as MockIndex, \
         patch("backend.indexing.index_manager.StorageContext") as MockSC:

        MockSC.from_defaults.return_value = MagicMock()
        mock_index = MagicMock()
        MockIndex.return_value = mock_index

        manager = IndexManager(vector_store=mock_vector_store, embed_model=mock_embed_model)
        index = manager.build_vector_index(nodes)

        assert index is not None
        assert manager._vector_index is mock_index

        # StorageContext must be built with our vector_store
        MockSC.from_defaults.assert_called_once_with(vector_store=mock_vector_store)
        # VectorStoreIndex must receive nodes and context
        MockIndex.assert_called_once()
        call_kwargs = MockIndex.call_args
        assert call_kwargs is not None


def test_build_vector_index_stores_index():
    """build_vector_index stores the result in self._vector_index."""
    mock_vector_store = MagicMock()
    mock_embed_model = MagicMock()
    nodes = [_make_node()]

    with patch("backend.indexing.index_manager.VectorStoreIndex") as MockIndex, \
         patch("backend.indexing.index_manager.StorageContext"):
        mock_index = MagicMock()
        MockIndex.return_value = mock_index

        manager = IndexManager(vector_store=mock_vector_store, embed_model=mock_embed_model)
        result = manager.build_vector_index(nodes)

        assert result is mock_index
        assert manager._vector_index is mock_index


# ---------------------------------------------------------------------------
# test_build_summary_index
# ---------------------------------------------------------------------------

def test_build_summary_index():
    """build_summary_index calls DocumentSummaryIndex.from_documents with llm and embed_model."""
    mock_vector_store = MagicMock()
    mock_embed_model = MagicMock()
    mock_llm = MagicMock()
    nodes = [_make_node("Some content", "node-1")]

    with patch("backend.indexing.index_manager.DocumentSummaryIndex") as MockDSI, \
         patch("backend.indexing.index_manager.Document") as MockDocument:
        mock_index = MagicMock()
        MockDSI.from_documents.return_value = mock_index
        MockDocument.side_effect = lambda text: MagicMock(text=text)

        manager = IndexManager(
            vector_store=mock_vector_store,
            embed_model=mock_embed_model,
            llm=mock_llm,
        )
        index = manager.build_summary_index(nodes)

        assert index is not None
        assert manager._summary_index is mock_index

        # from_documents must be called with llm and embed_model
        MockDSI.from_documents.assert_called_once()
        call_kwargs = MockDSI.from_documents.call_args
        args, kwargs = call_kwargs
        assert kwargs.get("llm") is mock_llm
        assert kwargs.get("embed_model") is mock_embed_model


def test_build_summary_index_converts_nodes_to_documents():
    """build_summary_index converts nodes to Document objects before indexing."""
    mock_vector_store = MagicMock()
    mock_embed_model = MagicMock()
    nodes = [_make_node("Content A", "n1"), _make_node("Content B", "n2")]

    with patch("backend.indexing.index_manager.DocumentSummaryIndex") as MockDSI, \
         patch("backend.indexing.index_manager.Document") as MockDocument:
        mock_index = MagicMock()
        MockDSI.from_documents.return_value = mock_index

        manager = IndexManager(vector_store=mock_vector_store, embed_model=mock_embed_model)
        manager.build_summary_index(nodes)

        # Document should have been created once for each node
        assert MockDocument.call_count == len(nodes)


def test_build_summary_index_stores_index():
    """build_summary_index stores the result in self._summary_index."""
    mock_vector_store = MagicMock()
    mock_embed_model = MagicMock()
    nodes = [_make_node()]

    with patch("backend.indexing.index_manager.DocumentSummaryIndex") as MockDSI, \
         patch("backend.indexing.index_manager.Document"):
        mock_index = MagicMock()
        MockDSI.from_documents.return_value = mock_index

        manager = IndexManager(vector_store=mock_vector_store, embed_model=mock_embed_model)
        result = manager.build_summary_index(nodes)

        assert result is mock_index
        assert manager._summary_index is mock_index


# ---------------------------------------------------------------------------
# test_load_existing_vector_index
# ---------------------------------------------------------------------------

def test_load_existing_vector_index():
    """load_existing_vector_index calls VectorStoreIndex.from_vector_store."""
    mock_vector_store = MagicMock()
    mock_embed_model = MagicMock()

    with patch("backend.indexing.index_manager.VectorStoreIndex") as MockIndex:
        mock_index = MagicMock()
        MockIndex.from_vector_store.return_value = mock_index

        manager = IndexManager(vector_store=mock_vector_store, embed_model=mock_embed_model)
        result = manager.load_existing_vector_index()

        assert result is mock_index
        assert manager._vector_index is mock_index
        MockIndex.from_vector_store.assert_called_once_with(mock_vector_store)


def test_load_existing_vector_index_stores_index():
    """load_existing_vector_index stores loaded index in self._vector_index."""
    mock_vector_store = MagicMock()
    mock_embed_model = MagicMock()

    with patch("backend.indexing.index_manager.VectorStoreIndex") as MockIndex:
        mock_index = MagicMock()
        MockIndex.from_vector_store.return_value = mock_index

        manager = IndexManager(vector_store=mock_vector_store, embed_model=mock_embed_model)
        manager.load_existing_vector_index()

        assert manager._vector_index is mock_index


# ---------------------------------------------------------------------------
# test_get_query_engine_no_indexes_raises
# ---------------------------------------------------------------------------

def test_get_query_engine_no_indexes_raises():
    """get_query_engine raises RuntimeError when no indexes are available."""
    manager = IndexManager(vector_store=MagicMock(), embed_model=MagicMock())
    # Neither _vector_index nor _summary_index is set

    with pytest.raises(RuntimeError, match="No indexes available"):
        manager.get_query_engine()


# ---------------------------------------------------------------------------
# test_get_query_engine_single_index
# ---------------------------------------------------------------------------

def test_get_query_engine_single_vector_index():
    """get_query_engine returns query engine directly when only vector index exists."""
    manager = IndexManager(vector_store=MagicMock(), embed_model=MagicMock())

    mock_vector_index = MagicMock()
    mock_qe = MagicMock()
    mock_vector_index.as_query_engine.return_value = mock_qe
    manager._vector_index = mock_vector_index

    with patch("backend.indexing.index_manager.RouterQueryEngine") as MockRouter:
        result = manager.get_query_engine()

    # Direct query engine, not RouterQueryEngine
    MockRouter.from_defaults.assert_not_called()
    assert result is mock_qe


def test_get_query_engine_single_summary_index():
    """get_query_engine returns query engine directly when only summary index exists."""
    manager = IndexManager(vector_store=MagicMock(), embed_model=MagicMock())

    mock_summary_index = MagicMock()
    mock_qe = MagicMock()
    mock_summary_index.as_query_engine.return_value = mock_qe
    manager._summary_index = mock_summary_index

    with patch("backend.indexing.index_manager.RouterQueryEngine") as MockRouter:
        result = manager.get_query_engine()

    MockRouter.from_defaults.assert_not_called()
    assert result is mock_qe


# ---------------------------------------------------------------------------
# test_get_query_engine_multiple_indexes
# ---------------------------------------------------------------------------

def test_get_query_engine_multiple_indexes():
    """get_query_engine creates RouterQueryEngine when both indexes exist."""
    manager = IndexManager(
        vector_store=MagicMock(), embed_model=MagicMock(), llm=MagicMock()
    )

    mock_vector_index = MagicMock()
    mock_summary_index = MagicMock()
    manager._vector_index = mock_vector_index
    manager._summary_index = mock_summary_index

    mock_router_engine = MagicMock()

    with patch("backend.indexing.index_manager.RouterQueryEngine") as MockRouter, \
         patch("backend.indexing.index_manager.LLMSingleSelector") as MockSelector, \
         patch("backend.indexing.index_manager.QueryEngineTool") as MockTool:
        MockRouter.from_defaults.return_value = mock_router_engine
        MockSelector.from_defaults.return_value = MagicMock()

        result = manager.get_query_engine()

    MockRouter.from_defaults.assert_called_once()
    assert result is mock_router_engine


def test_get_query_engine_multiple_indexes_uses_llm_selector():
    """get_query_engine uses LLMSingleSelector when multiple indexes are available."""
    manager = IndexManager(
        vector_store=MagicMock(), embed_model=MagicMock(), llm=MagicMock()
    )
    manager._vector_index = MagicMock()
    manager._summary_index = MagicMock()

    with patch("backend.indexing.index_manager.RouterQueryEngine") as MockRouter, \
         patch("backend.indexing.index_manager.LLMSingleSelector") as MockSelector, \
         patch("backend.indexing.index_manager.QueryEngineTool"):
        MockRouter.from_defaults.return_value = MagicMock()
        mock_selector = MagicMock()
        MockSelector.from_defaults.return_value = mock_selector

        manager.get_query_engine()

    MockSelector.from_defaults.assert_called_once()
    # RouterQueryEngine.from_defaults must receive the selector
    router_call_kwargs = MockRouter.from_defaults.call_args
    args, kwargs = router_call_kwargs
    assert kwargs.get("selector") is mock_selector


def test_get_query_engine_multiple_indexes_creates_two_tools():
    """get_query_engine creates exactly two QueryEngineTool instances for two indexes."""
    manager = IndexManager(
        vector_store=MagicMock(), embed_model=MagicMock(), llm=MagicMock()
    )
    manager._vector_index = MagicMock()
    manager._summary_index = MagicMock()

    with patch("backend.indexing.index_manager.RouterQueryEngine") as MockRouter, \
         patch("backend.indexing.index_manager.LLMSingleSelector"), \
         patch("backend.indexing.index_manager.QueryEngineTool") as MockTool:
        MockRouter.from_defaults.return_value = MagicMock()

        manager.get_query_engine()

    # Two tools: one for vector, one for summary
    assert MockTool.call_count == 2


def test_get_query_engine_tool_descriptions():
    """get_query_engine uses the correct descriptions for each tool."""
    manager = IndexManager(
        vector_store=MagicMock(), embed_model=MagicMock(), llm=MagicMock()
    )
    manager._vector_index = MagicMock()
    manager._summary_index = MagicMock()

    with patch("backend.indexing.index_manager.RouterQueryEngine") as MockRouter, \
         patch("backend.indexing.index_manager.LLMSingleSelector"), \
         patch("backend.indexing.index_manager.QueryEngineTool") as MockTool:
        MockRouter.from_defaults.return_value = MagicMock()

        manager.get_query_engine()

    all_calls = MockTool.call_args_list
    descriptions = [c[1].get("description", "") for c in all_calls]

    assert any("specific facts" in d or "semantic similarity" in d for d in descriptions), \
        "Expected vector index description"
    assert any("summarization" in d or "overview" in d for d in descriptions), \
        "Expected summary index description"
