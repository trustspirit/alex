from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, call

import pytest


@pytest.fixture
def deps():
    """Create all mock dependencies for SyncManager."""
    r2 = MagicMock()
    doc_repo = MagicMock()
    collection_repo = MagicMock()
    tag_repo = MagicMock()
    chroma_store = MagicMock()
    settings_repo = MagicMock()
    return {
        "r2_client": r2,
        "document_repo": doc_repo,
        "collection_repo": collection_repo,
        "tag_repo": tag_repo,
        "chroma_store": chroma_store,
        "settings_repo": settings_repo,
    }


@pytest.fixture
def sync_manager(deps):
    from backend.sync.sync_manager import SyncManager
    return SyncManager(**deps)


def _make_doc(doc_id=1, title="test.pdf", source_type="pdf",
              source_path="/tmp/test.pdf", collection_id=None,
              token_count=100, fallback_used=False, fallback_warning=None,
              sync_status="pending", synced_at=None, status="completed"):
    doc = MagicMock()
    doc.id = doc_id
    doc.title = title
    doc.source_type = source_type
    doc.source_path = source_path
    doc.collection_id = collection_id
    doc.token_count = token_count
    doc.fallback_used = fallback_used
    doc.fallback_warning = fallback_warning
    doc.sync_status = sync_status
    doc.synced_at = synced_at
    doc.status = status
    doc.tags = []
    return doc


def _make_collection(coll_id=1, name="Research", description="Papers"):
    coll = MagicMock()
    coll.id = coll_id
    coll.name = name
    coll.description = description
    return coll


# --- Push tests ---

def test_push_document_uploads_to_r2(sync_manager, deps):
    doc = _make_doc()
    deps["document_repo"].get_by_id.return_value = doc
    chroma_coll = MagicMock()
    chroma_coll.get.return_value = {
        "ids": ["n1"], "embeddings": [[0.1, 0.2]],
        "metadatas": [{"source": "/tmp/test.pdf"}], "documents": ["chunk"],
    }
    deps["chroma_store"].get_or_create_collection.return_value = chroma_coll

    sync_manager.push_document(1)

    # upload called twice: once for document, once for manifest
    assert deps["r2_client"].upload.call_count == 2
    key = deps["r2_client"].upload.call_args_list[0][0][0]
    assert key == "documents/1.json.gz"


def test_push_document_replaces_source_path(sync_manager, deps):
    doc = _make_doc(source_path="/Users/me/Documents/test.pdf")
    deps["document_repo"].get_by_id.return_value = doc
    chroma_coll = MagicMock()
    chroma_coll.get.return_value = {
        "ids": ["n1"], "embeddings": [[0.1]],
        "metadatas": [{"source": "/Users/me/Documents/test.pdf"}],
        "documents": ["text"],
    }
    deps["chroma_store"].get_or_create_collection.return_value = chroma_coll

    sync_manager.push_document(1)

    # First upload call is the document, second is the manifest
    upload_data = deps["r2_client"].upload.call_args_list[0][0][1]
    assert upload_data["metadata"]["source_path"] == "test.pdf"
    assert upload_data["vectors"]["metadatas"][0]["source"] == "test.pdf"


def test_push_document_sets_synced_at(sync_manager, deps):
    doc = _make_doc()
    doc.synced_at = None
    deps["document_repo"].get_by_id.return_value = doc
    chroma_coll = MagicMock()
    chroma_coll.get.return_value = {
        "ids": [], "embeddings": [], "metadatas": [], "documents": [],
    }
    deps["chroma_store"].get_or_create_collection.return_value = chroma_coll

    sync_manager.push_document(1)

    assert doc.synced_at is not None
    assert doc.sync_status == "synced"


def test_push_failure_records_pending(sync_manager, deps):
    doc = _make_doc()
    deps["document_repo"].get_by_id.return_value = doc
    chroma_coll = MagicMock()
    chroma_coll.get.return_value = {
        "ids": [], "embeddings": [], "metadatas": [], "documents": [],
    }
    deps["chroma_store"].get_or_create_collection.return_value = chroma_coll
    deps["r2_client"].upload.side_effect = Exception("Network error")

    sync_manager.push_document(1)
    # Should not raise, should log warning


# --- Delete tests ---

def test_push_delete_removes_from_r2(sync_manager, deps):
    sync_manager.push_delete(1)
    deps["r2_client"].delete.assert_called_with("documents/1.json.gz")


def test_push_delete_adds_tombstone(sync_manager, deps):
    sync_manager.push_delete(1)
    deps["r2_client"].upload.assert_called()  # manifest upload
    key = deps["r2_client"].upload.call_args[0][0]
    assert key == "manifest.json"


def test_push_delete_failure_does_not_raise(sync_manager, deps):
    deps["r2_client"].delete.side_effect = Exception("Network error")
    sync_manager.push_delete(1)  # Should not raise


# --- Pull tests ---

def test_pull_downloads_new_documents(sync_manager, deps):
    deps["r2_client"].list_objects.return_value = ["documents/99.json.gz"]
    deps["r2_client"].download.side_effect = [
        # manifest
        {"version": 1, "last_updated": "", "documents": {
            "99": {"title": "remote.pdf", "source_type": "pdf", "synced_at": "2026-01-01T00:00:00Z"},
        }, "collections": {}, "tombstones": {}},
        # document
        {"metadata": {
            "id": "99", "title": "remote.pdf", "source_type": "pdf",
            "source_path": "remote.pdf", "collection_name": None,
            "tags": [], "token_count": 50,
            "fallback_used": False, "fallback_warning": None,
        }, "vectors": {
            "ids": ["n1"], "embeddings": [[0.1]],
            "metadatas": [{"source": "remote.pdf"}], "documents": ["text"],
        }},
    ]
    deps["document_repo"].list_all.return_value = []

    chroma_coll = MagicMock()
    deps["chroma_store"].get_or_create_collection.return_value = chroma_coll

    sync_manager.pull()

    deps["document_repo"].create.assert_called_once()
    chroma_coll.upsert.assert_called_once()


def test_pull_applies_tombstones(sync_manager, deps):
    local_doc = _make_doc(doc_id=5, sync_status="synced")
    deps["r2_client"].list_objects.return_value = []
    deps["r2_client"].download.side_effect = [
        {"version": 1, "last_updated": "", "documents": {},
         "collections": {}, "tombstones": {
            "5": {"deleted_at": "2026-01-01T00:00:00Z"},
        }},
    ]
    deps["document_repo"].list_all.return_value = [local_doc]

    sync_manager.pull()

    deps["document_repo"].delete.assert_called_with(5)


def test_pull_creates_missing_collections(sync_manager, deps):
    deps["r2_client"].list_objects.return_value = ["documents/10.json.gz"]
    deps["r2_client"].download.side_effect = [
        {"version": 1, "last_updated": "", "documents": {
            "10": {"title": "t", "source_type": "pdf", "synced_at": "2026-01-01T00:00:00Z"},
        }, "collections": {"NewCol": {"description": "new"}}, "tombstones": {}},
        {"metadata": {
            "id": "10", "title": "t", "source_type": "pdf",
            "source_path": "t.pdf", "collection_name": "NewCol",
            "tags": [], "token_count": 10,
            "fallback_used": False, "fallback_warning": None,
        }, "vectors": {
            "ids": [], "embeddings": [], "metadatas": [], "documents": [],
        }},
    ]
    deps["document_repo"].list_all.return_value = []
    deps["collection_repo"].list_all.return_value = []
    new_coll = _make_collection(coll_id=2, name="NewCol")
    deps["collection_repo"].create.return_value = new_coll

    chroma_coll = MagicMock()
    deps["chroma_store"].get_or_create_collection.return_value = chroma_coll

    sync_manager.pull()

    deps["collection_repo"].create.assert_called_with("NewCol", "new")


def test_pull_skips_failed_downloads(sync_manager, deps):
    deps["r2_client"].list_objects.return_value = ["documents/1.json.gz", "documents/2.json.gz"]
    deps["r2_client"].download.side_effect = [
        {"version": 1, "last_updated": "", "documents": {
            "1": {"title": "a", "source_type": "pdf", "synced_at": "2026-01-01T00:00:00Z"},
            "2": {"title": "b", "source_type": "pdf", "synced_at": "2026-01-01T00:00:00Z"},
        }, "collections": {}, "tombstones": {}},
        Exception("Download failed"),  # doc 1 fails
        {"metadata": {
            "id": "2", "title": "b", "source_type": "pdf",
            "source_path": "b.pdf", "collection_name": None,
            "tags": [], "token_count": 10,
            "fallback_used": False, "fallback_warning": None,
        }, "vectors": {
            "ids": ["n1"], "embeddings": [[0.1]],
            "metadatas": [{"source": "b.pdf"}], "documents": ["text"],
        }},
    ]
    deps["document_repo"].list_all.return_value = []
    chroma_coll = MagicMock()
    deps["chroma_store"].get_or_create_collection.return_value = chroma_coll

    sync_manager.pull()  # Should not raise

    # Only doc 2 should be created
    assert deps["document_repo"].create.call_count == 1


# --- Full sync tests ---

def test_full_sync_pull_then_push(sync_manager, deps):
    """Verify pull is called, then unsynced docs are pushed."""
    # Set up pull to be a no-op (no remote docs)
    deps["r2_client"].list_objects.return_value = []
    deps["r2_client"].download.side_effect = [
        {"version": 1, "last_updated": "", "documents": {},
         "collections": {}, "tombstones": {}},
    ]

    # First call to list_all is from pull, second from full_sync's push loop
    unsynced_doc = _make_doc(doc_id=10, status="completed", synced_at=None)
    already_synced_doc = _make_doc(doc_id=11, status="completed",
                                   synced_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
    pending_doc = _make_doc(doc_id=12, status="pending", synced_at=None)
    deps["document_repo"].list_all.return_value = [unsynced_doc, already_synced_doc, pending_doc]
    deps["document_repo"].get_by_id.return_value = unsynced_doc

    chroma_coll = MagicMock()
    chroma_coll.get.return_value = {
        "ids": [], "embeddings": [], "metadatas": [], "documents": [],
    }
    deps["chroma_store"].get_or_create_collection.return_value = chroma_coll

    result = {}

    def capture(data):
        result.update(data)

    sync_manager.full_sync(on_complete=capture)

    # Only the unsynced completed doc should be pushed
    deps["document_repo"].get_by_id.assert_called_with(10)
    assert result["pushed"] == 1


def test_full_sync_captures_pull_counts(sync_manager, deps):
    """Verify on_complete receives real pull counts, not zeros."""
    deps["r2_client"].list_objects.return_value = ["documents/99.json.gz"]
    deps["r2_client"].download.side_effect = [
        # manifest
        {"version": 1, "last_updated": "", "documents": {
            "99": {"title": "remote.pdf", "source_type": "pdf",
                   "synced_at": "2026-01-01T00:00:00Z"},
        }, "collections": {}, "tombstones": {}},
        # document payload
        {"metadata": {
            "id": "99", "title": "remote.pdf", "source_type": "pdf",
            "source_path": "remote.pdf", "collection_name": None,
            "tags": [], "token_count": 50,
            "fallback_used": False, "fallback_warning": None,
        }, "vectors": {
            "ids": ["n1"], "embeddings": [[0.1]],
            "metadatas": [{"source": "remote.pdf"}], "documents": ["text"],
        }},
    ]
    deps["document_repo"].list_all.return_value = []

    chroma_coll = MagicMock()
    deps["chroma_store"].get_or_create_collection.return_value = chroma_coll

    result = {}

    def capture(data):
        result.update(data)

    sync_manager.full_sync(on_complete=capture)

    assert result["added"] == 1
    assert result["deleted"] == 0
    assert result["pushed"] == 0
