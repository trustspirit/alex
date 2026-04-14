from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Determine whether chromadb is available on this machine.
# If not, inject a lightweight mock so every test can still run.
# ---------------------------------------------------------------------------
try:
    import chromadb  # noqa: F401
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

    # Build a minimal mock that satisfies ChromaStore's usage
    _mock_chromadb = MagicMock()

    def _make_collection(name: str):
        coll = MagicMock()
        coll.name = name
        return coll

    _collections: dict[str, MagicMock] = {}

    def _get_or_create(name: str):
        if name not in _collections:
            _collections[name] = _make_collection(name)
        return _collections[name]

    def _delete_collection(name: str):
        _collections.pop(name, None)

    def _list_collections():
        return list(_collections.values())

    _mock_client = MagicMock()
    _mock_client.get_or_create_collection.side_effect = _get_or_create
    _mock_client.delete_collection.side_effect = _delete_collection
    _mock_client.list_collections.side_effect = _list_collections

    _mock_chromadb.PersistentClient.return_value = _mock_client
    sys.modules["chromadb"] = _mock_chromadb

    # Also mock llama_index chroma vector store
    _mock_chroma_vs_module = MagicMock()
    _mock_chroma_vs_module.ChromaVectorStore = MagicMock(
        side_effect=lambda chroma_collection: MagicMock(name="ChromaVectorStore")
    )
    sys.modules.setdefault(
        "llama_index.vector_stores.chroma", _mock_chroma_vs_module
    )


# Import after mocks are in place
from backend.indexing.store import ChromaStore  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_mock_collections():
    """Reset the in-process collection store between tests when chromadb is mocked."""
    if not CHROMADB_AVAILABLE:
        _collections.clear()
    yield
    if not CHROMADB_AVAILABLE:
        _collections.clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_create_collection(tmp_data_dir):
    store = ChromaStore(persist_dir=str(tmp_data_dir / "chroma"))
    chroma_coll = store.get_or_create_collection("test_collection")
    assert chroma_coll is not None


def test_get_vector_store(tmp_data_dir):
    store = ChromaStore(persist_dir=str(tmp_data_dir / "chroma"))
    vs = store.get_vector_store("test_collection")
    assert vs is not None


def test_delete_collection(tmp_data_dir):
    store = ChromaStore(persist_dir=str(tmp_data_dir / "chroma"))
    store.get_or_create_collection("to_delete")
    store.delete_collection("to_delete")
    # Verify it's gone
    collections = store.list_collections()
    names = [c.name for c in collections]
    assert "to_delete" not in names


def test_get_or_create_is_idempotent(tmp_data_dir):
    store = ChromaStore(persist_dir=str(tmp_data_dir / "chroma"))
    c1 = store.get_or_create_collection("same")
    c2 = store.get_or_create_collection("same")
    # Should be the same collection
    assert c1.name == c2.name
