from __future__ import annotations

import pytest

from backend.storage.document_repo import DocumentRepo


def test_create(tmp_db):
    repo = DocumentRepo(tmp_db)
    doc = repo.create(
        title="My Paper",
        source_type="pdf",
        source_path="/path/to/paper.pdf",
    )
    assert doc.id is not None
    assert doc.title == "My Paper"
    assert doc.source_type == "pdf"
    assert doc.source_path == "/path/to/paper.pdf"
    assert doc.status == "pending"
    assert doc.token_count == 0
    assert doc.collection_id is None


def test_create_with_collection(tmp_db):
    from backend.storage.collection_repo import CollectionRepo

    col_repo = CollectionRepo(tmp_db)
    coll = col_repo.create(name="Science")

    repo = DocumentRepo(tmp_db)
    doc = repo.create(
        title="Paper in collection",
        source_type="pdf",
        source_path="/path/paper.pdf",
        collection_id=coll.id,
        token_count=500,
    )
    assert doc.collection_id == coll.id
    assert doc.token_count == 500


def test_update_status(tmp_db):
    repo = DocumentRepo(tmp_db)
    doc = repo.create(title="Doc", source_type="txt", source_path="/doc.txt")
    assert doc.status == "pending"

    updated = repo.update_status(doc.id, "completed")
    assert updated.status == "completed"

    fetched = repo.get_by_id(doc.id)
    assert fetched.status == "completed"


def test_set_fallback(tmp_db):
    repo = DocumentRepo(tmp_db)
    doc = repo.create(title="Doc", source_type="txt", source_path="/doc.txt")
    assert doc.fallback_used is False

    updated = repo.set_fallback(doc.id, "Used OCR fallback due to scanned PDF")
    assert updated.fallback_used is True
    assert updated.fallback_warning == "Used OCR fallback due to scanned PDF"


def test_list_by_collection(tmp_db):
    from backend.storage.collection_repo import CollectionRepo

    col_repo = CollectionRepo(tmp_db)
    coll = col_repo.create(name="ML")

    repo = DocumentRepo(tmp_db)
    doc1 = repo.create(title="Doc A", source_type="pdf", source_path="/a.pdf", collection_id=coll.id)
    doc2 = repo.create(title="Doc B", source_type="pdf", source_path="/b.pdf", collection_id=coll.id)
    doc3 = repo.create(title="Doc C", source_type="txt", source_path="/c.txt")  # no collection

    results = repo.list_by_collection(coll.id)
    assert len(results) == 2
    ids = {d.id for d in results}
    assert doc1.id in ids
    assert doc2.id in ids
    assert doc3.id not in ids


def test_delete(tmp_db):
    repo = DocumentRepo(tmp_db)
    doc = repo.create(title="To Delete", source_type="pdf", source_path="/del.pdf")
    doc_id = doc.id

    repo.delete(doc_id)
    assert repo.get_by_id(doc_id) is None


def test_total_tokens_for_collection(tmp_db):
    from backend.storage.collection_repo import CollectionRepo

    col_repo = CollectionRepo(tmp_db)
    coll = col_repo.create(name="Physics")

    repo = DocumentRepo(tmp_db)
    repo.create(title="Doc 1", source_type="pdf", source_path="/1.pdf", collection_id=coll.id, token_count=100)
    repo.create(title="Doc 2", source_type="pdf", source_path="/2.pdf", collection_id=coll.id, token_count=250)
    repo.create(title="Doc 3", source_type="txt", source_path="/3.txt", token_count=999)  # other collection

    total = repo.total_tokens_for_collection(coll.id)
    assert total == 350


def test_total_tokens_for_empty_collection(tmp_db):
    from backend.storage.collection_repo import CollectionRepo

    col_repo = CollectionRepo(tmp_db)
    coll = col_repo.create(name="Empty")

    repo = DocumentRepo(tmp_db)
    total = repo.total_tokens_for_collection(coll.id)
    assert total == 0


def test_set_token_count(tmp_db):
    repo = DocumentRepo(tmp_db)
    doc = repo.create(title="Doc", source_type="txt", source_path="/doc.txt")
    assert doc.token_count == 0

    updated = repo.set_token_count(doc.id, 1234)
    assert updated.token_count == 1234


def test_list_all_ordered_by_created_at_desc(tmp_db):
    repo = DocumentRepo(tmp_db)
    repo.create(title="First", source_type="txt", source_path="/first.txt")
    repo.create(title="Second", source_type="txt", source_path="/second.txt")
    repo.create(title="Third", source_type="txt", source_path="/third.txt")

    docs = repo.list_all()
    assert len(docs) == 3
    # Most recent first
    assert docs[0].title == "Third"
    assert docs[2].title == "First"
