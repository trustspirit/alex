from datetime import datetime, timezone, timedelta
import pytest


@pytest.fixture
def manifest():
    from backend.sync.manifest import Manifest
    return Manifest()


def test_add_document(manifest):
    manifest.add_document("doc-1", {"title": "Test", "source_type": "pdf"})
    assert "doc-1" in manifest.documents
    assert manifest.documents["doc-1"]["title"] == "Test"
    assert "synced_at" in manifest.documents["doc-1"]


def test_add_tombstone(manifest):
    manifest.add_tombstone("doc-2")
    assert "doc-2" in manifest.tombstones
    assert "deleted_at" in manifest.tombstones["doc-2"]


def test_clean_expired_tombstones(manifest):
    now = datetime.now(timezone.utc)
    manifest.tombstones = {
        "old": {"deleted_at": (now - timedelta(days=31)).isoformat()},
        "recent": {"deleted_at": (now - timedelta(days=5)).isoformat()},
    }
    manifest.clean_expired_tombstones(ttl_days=30)
    assert "old" not in manifest.tombstones
    assert "recent" in manifest.tombstones


def test_diff_new_remote_docs(manifest):
    manifest.documents = {
        "remote-1": {"title": "R1", "source_type": "pdf", "synced_at": "2026-01-01T00:00:00Z"},
        "remote-2": {"title": "R2", "source_type": "md", "synced_at": "2026-01-01T00:00:00Z"},
    }
    diff = manifest.diff(local_doc_ids={"remote-1"}, local_synced_ids={"remote-1"})
    assert "remote-2" in diff.to_download
    assert "remote-1" not in diff.to_download


def test_diff_tombstoned_docs(manifest):
    manifest.tombstones = {"local-1": {"deleted_at": "2026-01-01T00:00:00Z"}}
    diff = manifest.diff(local_doc_ids={"local-1"}, local_synced_ids=set())
    assert "local-1" in diff.to_delete_locally


def test_diff_local_unsynced(manifest):
    manifest.documents = {}
    diff = manifest.diff(local_doc_ids={"new-local"}, local_synced_ids=set())
    assert "new-local" in diff.to_upload


def test_diff_already_synced(manifest):
    manifest.documents = {
        "doc-1": {"title": "D1", "source_type": "pdf", "synced_at": "2026-01-01T00:00:00Z"},
    }
    diff = manifest.diff(local_doc_ids={"doc-1"}, local_synced_ids={"doc-1"})
    assert len(diff.to_download) == 0
    assert len(diff.to_upload) == 0
    assert len(diff.to_delete_locally) == 0


def test_set_collection(manifest):
    manifest.set_collection("연구자료", "AI 논문 모음")
    assert manifest.collections["연구자료"]["description"] == "AI 논문 모음"


def test_to_dict_and_from_dict(manifest):
    manifest.add_document("doc-1", {"title": "T", "source_type": "pdf"})
    manifest.set_collection("col-1", "desc")
    manifest.add_tombstone("doc-2")
    data = manifest.to_dict()
    from backend.sync.manifest import Manifest
    restored = Manifest.from_dict(data)
    assert "doc-1" in restored.documents
    assert "col-1" in restored.collections
    assert "doc-2" in restored.tombstones
