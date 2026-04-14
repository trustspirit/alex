from __future__ import annotations

from backend.storage.tag_repo import TagRepo
from backend.storage.models import Document


def test_create_tag(tmp_db):
    repo = TagRepo(tmp_db)
    tag = repo.create("AI")
    assert tag.id is not None
    assert tag.name == "AI"


def test_get_or_create_existing(tmp_db):
    repo = TagRepo(tmp_db)
    t1 = repo.get_or_create("ML")
    t2 = repo.get_or_create("ML")
    assert t1.id == t2.id


def test_add_tag_to_document(tmp_db):
    repo = TagRepo(tmp_db)
    doc = Document(title="Test", source_type="pdf", source_path="/test.pdf", status="completed")
    tmp_db.add(doc)
    tmp_db.commit()
    repo.add_tag_to_document(doc.id, "AI")
    tags = repo.get_tags_for_document(doc.id)
    assert len(tags) == 1
    assert tags[0].name == "AI"


def test_remove_tag_from_document(tmp_db):
    repo = TagRepo(tmp_db)
    doc = Document(title="Test", source_type="pdf", source_path="/test.pdf", status="completed")
    tmp_db.add(doc)
    tmp_db.commit()
    repo.add_tag_to_document(doc.id, "AI")
    tag = repo.list_all()[0]
    repo.remove_tag_from_document(doc.id, tag.id)
    tags = repo.get_tags_for_document(doc.id)
    assert len(tags) == 0


def test_list_all(tmp_db):
    repo = TagRepo(tmp_db)
    repo.create("B-tag")
    repo.create("A-tag")
    tags = repo.list_all()
    assert tags[0].name == "A-tag"  # ordered by name
