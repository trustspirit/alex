from __future__ import annotations

import pytest

from backend.storage.collection_repo import CollectionRepo


def test_create(tmp_db):
    repo = CollectionRepo(tmp_db)
    coll = repo.create(name="AI Research", description="Papers on AI")
    assert coll.id is not None
    assert coll.name == "AI Research"
    assert coll.description == "Papers on AI"
    assert coll.created_at is not None


def test_create_no_description(tmp_db):
    repo = CollectionRepo(tmp_db)
    coll = repo.create(name="Empty Collection")
    assert coll.description == ""


def test_list_all(tmp_db):
    repo = CollectionRepo(tmp_db)
    repo.create(name="Zebra Collection")
    repo.create(name="Apple Collection")
    repo.create(name="Mango Collection")

    collections = repo.list_all()
    assert len(collections) == 3
    # Should be ordered by name
    names = [c.name for c in collections]
    assert names == sorted(names)


def test_rename(tmp_db):
    repo = CollectionRepo(tmp_db)
    coll = repo.create(name="Old Name")

    renamed = repo.rename(coll.id, "New Name")
    assert renamed.name == "New Name"

    fetched = repo.get_by_id(coll.id)
    assert fetched.name == "New Name"


def test_delete(tmp_db):
    repo = CollectionRepo(tmp_db)
    coll = repo.create(name="To Delete")
    coll_id = coll.id

    repo.delete(coll_id)
    assert repo.get_by_id(coll_id) is None


def test_get_by_id_nonexistent(tmp_db):
    repo = CollectionRepo(tmp_db)
    result = repo.get_by_id(9999)
    assert result is None
