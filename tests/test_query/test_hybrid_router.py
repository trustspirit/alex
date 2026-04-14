from __future__ import annotations

import pytest

from backend.query.hybrid_router import HybridRouter


class TestHybridRouterDecide:
    """Tests for HybridRouter.decide()."""

    def test_small_collection_scoped_returns_full_context(self):
        """5000 tokens, scoped → full_context."""
        router = HybridRouter(threshold_tokens=8000)
        result = router.decide(total_tokens=5000, collection_scoped=True)
        assert result == "full_context"

    def test_large_collection_scoped_returns_rag(self):
        """50000 tokens, scoped → rag."""
        router = HybridRouter(threshold_tokens=8000)
        result = router.decide(total_tokens=50000, collection_scoped=True)
        assert result == "rag"

    def test_unscoped_always_returns_rag(self):
        """Unscoped always → rag, regardless of token count."""
        router = HybridRouter(threshold_tokens=8000)
        assert router.decide(total_tokens=100, collection_scoped=False) == "rag"
        assert router.decide(total_tokens=5000, collection_scoped=False) == "rag"
        assert router.decide(total_tokens=50000, collection_scoped=False) == "rag"

    def test_boundary_at_threshold_returns_full_context(self):
        """Exactly at threshold (8000) → full_context."""
        router = HybridRouter(threshold_tokens=8000)
        result = router.decide(total_tokens=8000, collection_scoped=True)
        assert result == "full_context"

    def test_one_above_threshold_returns_rag(self):
        """One token above threshold (8001) → rag."""
        router = HybridRouter(threshold_tokens=8000)
        result = router.decide(total_tokens=8001, collection_scoped=True)
        assert result == "rag"

    def test_custom_threshold(self):
        """Custom threshold is respected."""
        router = HybridRouter(threshold_tokens=1000)
        assert router.decide(total_tokens=999, collection_scoped=True) == "full_context"
        assert router.decide(total_tokens=1000, collection_scoped=True) == "full_context"
        assert router.decide(total_tokens=1001, collection_scoped=True) == "rag"

    def test_default_threshold_is_8000(self):
        """Default threshold is 8000."""
        router = HybridRouter()
        assert router._threshold == 8000
