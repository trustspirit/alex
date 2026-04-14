from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from backend.query.query_engine import QueryEngine
from backend.query.hybrid_router import HybridRouter


def _make_mock_response(answer: str = "42", source_nodes=None):
    """Create a mock LlamaIndex query response."""
    mock_response = MagicMock()
    mock_response.response = answer
    mock_response.source_nodes = source_nodes or []
    return mock_response


class TestQueryEngineInit:
    """Tests for QueryEngine initialisation."""

    def test_default_router_is_hybrid_router(self):
        """When no hybrid_router is supplied, a HybridRouter is created."""
        engine = QueryEngine(
            index_manager=MagicMock(),
            llm=MagicMock(),
            document_repo=MagicMock(),
        )
        assert isinstance(engine._router, HybridRouter)

    def test_custom_router_is_used(self):
        """Custom router is stored as-is."""
        custom_router = MagicMock()
        engine = QueryEngine(
            index_manager=MagicMock(),
            llm=MagicMock(),
            document_repo=MagicMock(),
            hybrid_router=custom_router,
        )
        assert engine._router is custom_router


class TestQueryEngineQuery:
    """Tests for QueryEngine.query()."""

    def _build_engine(self, router_decision: str = "rag", total_tokens: int = 0):
        """Helper to build a QueryEngine with mocked dependencies."""
        mock_index_manager = MagicMock()
        mock_llm = MagicMock()
        mock_doc_repo = MagicMock()
        mock_doc_repo.total_tokens_for_collection.return_value = total_tokens

        mock_query_engine = MagicMock()
        mock_query_engine.query.return_value = _make_mock_response("Test answer")
        mock_index_manager.get_query_engine.return_value = mock_query_engine

        mock_router = MagicMock(spec=HybridRouter)
        mock_router.decide.return_value = router_decision

        engine = QueryEngine(
            index_manager=mock_index_manager,
            llm=mock_llm,
            document_repo=mock_doc_repo,
            hybrid_router=mock_router,
        )
        return engine, mock_doc_repo, mock_router, mock_query_engine

    def test_query_result_has_required_keys(self):
        """query() result contains answer, sources, sources_json, and mode."""
        engine, _, _, _ = self._build_engine()
        result = engine.query("What is the meaning of life?", collection_id=1)
        assert "answer" in result
        assert "sources" in result
        assert "sources_json" in result
        assert "mode" in result

    def test_query_without_collection_id_is_always_rag(self):
        """When no collection_id given, router.decide is called with collection_scoped=False."""
        engine, mock_doc_repo, mock_router, _ = self._build_engine()
        engine.query("No collection question")
        mock_router.decide.assert_called_once()
        call_kwargs = mock_router.decide.call_args
        # collection_scoped must be False
        assert call_kwargs.kwargs.get("collection_scoped") is False or call_kwargs.args[1] is False

    def test_query_with_collection_id_passes_token_count(self):
        """When collection_id given, router gets token count from document_repo."""
        engine, mock_doc_repo, mock_router, _ = self._build_engine(total_tokens=5000)
        mock_doc_repo.total_tokens_for_collection.return_value = 5000

        engine.query("Collection question", collection_id=42)

        mock_doc_repo.total_tokens_for_collection.assert_called_once_with(42)
        # Router must receive the real token count
        call_kwargs = mock_router.decide.call_args
        # total_tokens positional or keyword
        called_tokens = (
            call_kwargs.kwargs.get("total_tokens")
            if call_kwargs.kwargs.get("total_tokens") is not None
            else call_kwargs.args[0]
        )
        assert called_tokens == 5000

    def test_query_with_collection_id_is_scoped(self):
        """When collection_id is given, collection_scoped=True is passed to router."""
        engine, _, mock_router, _ = self._build_engine()
        engine.query("scoped question", collection_id=7)
        call_kwargs = mock_router.decide.call_args
        collection_scoped = (
            call_kwargs.kwargs.get("collection_scoped")
            if call_kwargs.kwargs.get("collection_scoped") is not None
            else call_kwargs.args[1]
        )
        assert collection_scoped is True

    def test_query_answer_comes_from_index_manager(self):
        """query() answer field is the response text from the LlamaIndex engine."""
        engine, _, _, mock_qe = self._build_engine()
        mock_qe.query.return_value = _make_mock_response("Deep thought answer")
        result = engine.query("What is the answer?", collection_id=1)
        assert result["answer"] == "Deep thought answer"

    def test_query_mode_reflects_router_decision(self):
        """mode in result matches what the router returned."""
        engine_rag, _, _, _ = self._build_engine(router_decision="rag")
        result_rag = engine_rag.query("q", collection_id=1)
        assert result_rag["mode"] == "rag"

        engine_fc, _, _, _ = self._build_engine(router_decision="full_context")
        result_fc = engine_fc.query("q", collection_id=1)
        assert result_fc["mode"] == "full_context"

    def test_sources_json_is_string(self):
        """sources_json in result is a JSON string."""
        import json
        engine, _, _, _ = self._build_engine()
        result = engine.query("test", collection_id=1)
        # Must be parseable JSON
        parsed = json.loads(result["sources_json"])
        assert isinstance(parsed, list)
