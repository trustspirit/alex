from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta


@dataclass
class SyncDiff:
    to_download: set[str] = field(default_factory=set)
    to_upload: set[str] = field(default_factory=set)
    to_delete_locally: set[str] = field(default_factory=set)


class Manifest:
    """Tracks sync state: documents, collections, tombstones."""

    def __init__(self) -> None:
        self.version: int = 1
        self.last_updated: str = ""
        self.documents: dict[str, dict] = {}
        self.collections: dict[str, dict] = {}
        self.tombstones: dict[str, dict] = {}

    def add_document(self, doc_id: str, metadata: dict) -> None:
        entry = dict(metadata)
        entry["synced_at"] = datetime.now(timezone.utc).isoformat()
        self.documents[doc_id] = entry

    def remove_document(self, doc_id: str) -> None:
        self.documents.pop(doc_id, None)

    def add_tombstone(self, doc_id: str) -> None:
        self.remove_document(doc_id)
        self.tombstones[doc_id] = {
            "deleted_at": datetime.now(timezone.utc).isoformat(),
        }

    def set_collection(self, name: str, description: str = "") -> None:
        self.collections[name] = {"description": description}

    def remove_collection(self, name: str) -> None:
        self.collections.pop(name, None)

    def clean_expired_tombstones(self, ttl_days: int = 30) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=ttl_days)
        expired = [
            doc_id
            for doc_id, ts in self.tombstones.items()
            if datetime.fromisoformat(ts["deleted_at"]) < cutoff
        ]
        for doc_id in expired:
            del self.tombstones[doc_id]

    def diff(self, local_doc_ids: set[str], local_synced_ids: set[str]) -> SyncDiff:
        remote_ids = set(self.documents.keys())
        tombstone_ids = set(self.tombstones.keys())
        to_download = remote_ids - local_doc_ids - tombstone_ids
        to_delete_locally = local_doc_ids & tombstone_ids
        to_upload = local_doc_ids - remote_ids - tombstone_ids - local_synced_ids
        return SyncDiff(
            to_download=to_download,
            to_upload=to_upload,
            to_delete_locally=to_delete_locally,
        )

    def to_dict(self) -> dict:
        self.last_updated = datetime.now(timezone.utc).isoformat()
        return {
            "version": self.version,
            "last_updated": self.last_updated,
            "documents": self.documents,
            "collections": self.collections,
            "tombstones": self.tombstones,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Manifest:
        m = cls()
        m.version = data.get("version", 1)
        m.last_updated = data.get("last_updated", "")
        m.documents = data.get("documents", {})
        m.collections = data.get("collections", {})
        m.tombstones = data.get("tombstones", {})
        return m
