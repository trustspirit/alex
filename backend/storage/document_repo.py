from __future__ import annotations

from sqlalchemy import func

from backend.storage.base_repo import BaseRepo
from backend.storage.models import Document


class DocumentRepo(BaseRepo):

    def create(
        self,
        title: str,
        source_type: str,
        source_path: str,
        collection_id: int | None = None,
        token_count: int = 0,
    ) -> Document:
        doc = Document(
            title=title,
            source_type=source_type,
            source_path=source_path,
            collection_id=collection_id,
            token_count=token_count,
        )
        self._session.add(doc)
        self._session.commit()
        self._session.refresh(doc)
        return doc

    def get_by_id(self, doc_id: int) -> Document | None:
        return self._session.query(Document).filter_by(id=doc_id).first()

    def list_all(self) -> list[Document]:
        return (
            self._session.query(Document)
            .order_by(Document.created_at.desc())
            .all()
        )

    def list_by_collection(self, collection_id: int) -> list[Document]:
        return (
            self._session.query(Document)
            .filter_by(collection_id=collection_id)
            .order_by(Document.created_at.desc())
            .all()
        )

    def update_status(self, doc_id: int, status: str) -> Document | None:
        doc = self.get_by_id(doc_id)
        if doc is None:
            return None
        doc.status = status
        self._session.commit()
        self._session.refresh(doc)
        return doc

    def set_fallback(self, doc_id: int, warning: str) -> Document | None:
        doc = self.get_by_id(doc_id)
        if doc is None:
            return None
        doc.fallback_used = True
        doc.fallback_warning = warning
        self._session.commit()
        self._session.refresh(doc)
        return doc

    def set_token_count(self, doc_id: int, token_count: int) -> Document | None:
        doc = self.get_by_id(doc_id)
        if doc is None:
            return None
        doc.token_count = token_count
        self._session.commit()
        self._session.refresh(doc)
        return doc

    def total_tokens_for_collection(self, collection_id: int) -> int:
        result = (
            self._session.query(func.sum(Document.token_count))
            .filter_by(collection_id=collection_id)
            .scalar()
        )
        return result if result is not None else 0

    def update_title(self, doc_id: int, title: str) -> None:
        doc = self.get_by_id(doc_id)
        if doc:
            doc.title = title
            self._session.commit()

    def update_status_and_reset(self, doc_id: int) -> None:
        """Reset document for re-indexing."""
        doc = self.get_by_id(doc_id)
        if doc:
            doc.status = "pending"
            doc.token_count = 0
            self._session.commit()

    def move_to_collection(self, doc_id: int, collection_id: int | None) -> None:
        """Move a document to a different collection."""
        doc = self.get_by_id(doc_id)
        if doc:
            doc.collection_id = collection_id
            self._session.commit()

    def delete(self, doc_id: int) -> None:
        doc = self.get_by_id(doc_id)
        if doc is not None:
            self._session.delete(doc)
            self._session.commit()
