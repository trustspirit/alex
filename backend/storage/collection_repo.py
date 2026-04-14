from __future__ import annotations

from sqlalchemy.orm import Session

from backend.storage.models import Collection


class CollectionRepo:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, name: str, description: str = "") -> Collection:
        coll = Collection(name=name, description=description)
        self._session.add(coll)
        self._session.commit()
        self._session.refresh(coll)
        return coll

    def get_by_id(self, coll_id: int) -> Collection | None:
        return self._session.query(Collection).filter_by(id=coll_id).first()

    def list_all(self) -> list[Collection]:
        return self._session.query(Collection).order_by(Collection.name).all()

    def rename(self, coll_id: int, new_name: str) -> Collection | None:
        coll = self.get_by_id(coll_id)
        if coll is None:
            return None
        coll.name = new_name
        self._session.commit()
        self._session.refresh(coll)
        return coll

    def delete(self, coll_id: int) -> None:
        coll = self.get_by_id(coll_id)
        if coll is not None:
            self._session.delete(coll)
            self._session.commit()
