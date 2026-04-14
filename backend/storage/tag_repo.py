from __future__ import annotations

from sqlalchemy.orm import Session

from backend.storage.models import Document, Tag, document_tags


class TagRepo:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, name: str) -> Tag:
        tag = Tag(name=name)
        self._session.add(tag)
        self._session.commit()
        return tag

    def get_or_create(self, name: str) -> Tag:
        tag = self._session.query(Tag).filter_by(name=name).first()
        if tag is None:
            tag = Tag(name=name)
            self._session.add(tag)
            self._session.commit()
        return tag

    def list_all(self) -> list[Tag]:
        return self._session.query(Tag).order_by(Tag.name).all()

    def delete(self, tag_id: int) -> None:
        tag = self._session.query(Tag).get(tag_id)
        if tag:
            self._session.delete(tag)
            self._session.commit()

    def add_tag_to_document(self, doc_id: int, tag_name: str) -> None:
        tag = self.get_or_create(tag_name)
        doc = self._session.query(Document).get(doc_id)
        if doc and tag not in doc.tags:
            doc.tags.append(tag)
            self._session.commit()

    def remove_tag_from_document(self, doc_id: int, tag_id: int) -> None:
        doc = self._session.query(Document).get(doc_id)
        tag = self._session.query(Tag).get(tag_id)
        if doc and tag and tag in doc.tags:
            doc.tags.remove(tag)
            self._session.commit()

    def get_tags_for_document(self, doc_id: int) -> list[Tag]:
        doc = self._session.query(Document).get(doc_id)
        return list(doc.tags) if doc else []
