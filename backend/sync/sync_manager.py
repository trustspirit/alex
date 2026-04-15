from __future__ import annotations

import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from backend.sync.manifest import Manifest
from backend.sync.r2_client import R2Client

logger = logging.getLogger(__name__)

MANIFEST_KEY = "manifest.json"
DOCUMENTS_PREFIX = "documents/"


class SyncManager:
    """Orchestrates push/pull/delete sync operations with R2."""

    def __init__(
        self,
        r2_client: R2Client,
        document_repo,
        collection_repo,
        tag_repo,
        chroma_store,
        settings_repo,
    ) -> None:
        self._r2 = r2_client
        self._doc_repo = document_repo
        self._coll_repo = collection_repo
        self._tag_repo = tag_repo
        self._chroma = chroma_store
        self._settings_repo = settings_repo
        self._manifest = Manifest()
        self._lock = threading.RLock()

    def push_document(self, doc_id: int) -> None:
        """Push a single document (metadata + vectors) to R2."""
        try:
            doc = self._doc_repo.get_by_id(doc_id)
            if not doc:
                logger.warning("push_document: doc %s not found", doc_id)
                return

            chroma_coll = self._chroma.get_or_create_collection("default")
            vectors = chroma_coll.get(
                where={"source": doc.source_path},
                include=["embeddings", "metadatas", "documents"],
            )

            filename = os.path.basename(doc.source_path)

            normalized_metadatas = []
            for meta in vectors.get("metadatas", []):
                m = dict(meta)
                if "source" in m:
                    m["source"] = filename
                normalized_metadatas.append(m)

            coll_name = None
            if doc.collection_id:
                coll = self._coll_repo.get_by_id(doc.collection_id)
                if coll:
                    coll_name = coll.name

            tags = [t.name for t in (doc.tags or [])]

            payload = {
                "metadata": {
                    "id": str(doc.id),
                    "title": doc.title,
                    "source_type": doc.source_type,
                    "source_path": filename,
                    "collection_name": coll_name,
                    "tags": tags,
                    "token_count": doc.token_count,
                    "fallback_used": doc.fallback_used,
                    "fallback_warning": doc.fallback_warning,
                },
                "vectors": {
                    "ids": vectors.get("ids", []),
                    "embeddings": vectors.get("embeddings", []),
                    "metadatas": normalized_metadatas,
                    "documents": vectors.get("documents", []),
                },
            }

            key = f"{DOCUMENTS_PREFIX}{doc_id}.json.gz"
            self._r2.upload(key, payload)

            with self._lock:
                self._manifest.add_document(str(doc_id), {
                    "title": doc.title,
                    "source_type": doc.source_type,
                })
                self._upload_manifest()

            self._doc_repo.set_sync_status(doc_id, "synced")

            logger.info("push_document %s OK", doc_id)

        except Exception as exc:
            logger.warning("push_document %s FAILED: %s", doc_id, exc)

    def push_delete(self, doc_id: int) -> None:
        """Push a delete tombstone to R2."""
        try:
            key = f"{DOCUMENTS_PREFIX}{doc_id}.json.gz"
            try:
                self._r2.delete(key)
            except Exception as exc:
                logger.warning("Could not delete %s from R2: %s", key, exc)

            with self._lock:
                self._manifest.add_tombstone(str(doc_id))
                self._upload_manifest()

            logger.info("push_delete %s OK", doc_id)

        except Exception as exc:
            logger.warning("push_delete %s FAILED: %s", doc_id, exc)

    def push_manifest(self) -> None:
        """Upload current manifest to R2 (e.g. after collection changes)."""
        try:
            collections = self._coll_repo.list_all()
            self._manifest.collections = {}
            for c in collections:
                self._manifest.set_collection(c.name, c.description or "")

            with self._lock:
                self._upload_manifest()
        except Exception as exc:
            logger.warning("push_manifest FAILED: %s", exc)

    def pull(self, on_complete=None, on_error=None) -> None:
        """Pull remote state and merge into local."""
        try:
            remote_keys = self._r2.list_objects(DOCUMENTS_PREFIX)
            remote_doc_ids = set()
            for key in remote_keys:
                basename = key.replace(DOCUMENTS_PREFIX, "").replace(".json.gz", "")
                if basename:
                    remote_doc_ids.add(basename)

            try:
                manifest_data = self._r2.download(MANIFEST_KEY)
                self._manifest = Manifest.from_dict(manifest_data)
            except Exception:
                logger.info("No manifest found, using empty manifest")
                self._manifest = Manifest()

            local_docs = self._doc_repo.list_all()
            local_doc_ids = {str(d.id) for d in local_docs}
            local_synced_ids = {str(d.id) for d in local_docs if d.synced_at is not None}

            diff = self._manifest.diff(local_doc_ids, local_synced_ids)

            for rid in remote_doc_ids:
                if rid not in local_doc_ids and rid not in self._manifest.tombstones:
                    diff.to_download.add(rid)

            self._sync_collections()

            downloaded = []
            if diff.to_download:
                with ThreadPoolExecutor(max_workers=5) as pool:
                    futures = {}
                    for doc_id in diff.to_download:
                        key = f"{DOCUMENTS_PREFIX}{doc_id}.json.gz"
                        futures[doc_id] = pool.submit(self._safe_download, key)

                    for doc_id, future in futures.items():
                        try:
                            data = future.result()
                            if data is not None:
                                downloaded.append((doc_id, data))
                        except Exception as exc:
                            logger.warning("Pull download failed for %s: %s", doc_id, exc)

            added = 0
            for doc_id, data in downloaded:
                try:
                    self._insert_pulled_document(doc_id, data)
                    added += 1
                except Exception as exc:
                    logger.warning("Pull insert failed for %s: %s", doc_id, exc)

            deleted = 0
            for doc_id in diff.to_delete_locally:
                try:
                    int_id = int(doc_id)
                    doc = self._doc_repo.get_by_id(int_id)
                    if doc and self._chroma:
                        try:
                            self._chroma.delete_documents_by_source("default", doc.source_path)
                        except Exception:
                            pass
                    self._doc_repo.delete(int_id)
                    deleted += 1
                except Exception as exc:
                    logger.warning("Pull delete failed for %s: %s", doc_id, exc)

            with self._lock:
                self._manifest.clean_expired_tombstones(ttl_days=30)
                self._upload_manifest()

            logger.info("Pull complete: added=%d, deleted=%d", added, deleted)

            if on_complete:
                on_complete({"added": added, "deleted": deleted})

        except Exception as exc:
            logger.error("Pull failed: %s", exc)
            if on_error:
                on_error({
                    "category": "network",
                    "message": str(exc),
                    "recoverable": True,
                    "action": "retry",
                    "action_label": "Retry",
                })

    def full_sync(self, on_complete=None, on_error=None) -> None:
        """Full sync: pull then push unsynced local docs."""
        with self._lock:
            pull_result = {"added": 0, "deleted": 0}

            def _capture_pull_result(data):
                pull_result.update(data)

            self.pull(on_complete=_capture_pull_result, on_error=on_error)

            pushed = 0
            local_docs = self._doc_repo.list_all()
            for doc in local_docs:
                if doc.status == "completed" and doc.synced_at is None:
                    self.push_document(doc.id)
                    pushed += 1

            if on_complete:
                on_complete({"added": pull_result["added"], "deleted": pull_result["deleted"], "pushed": pushed})

    def _upload_manifest(self) -> None:
        try:
            self._r2.upload(MANIFEST_KEY, self._manifest.to_dict())
        except Exception as exc:
            logger.warning("Manifest upload failed: %s", exc)

    def _safe_download(self, key: str):
        try:
            return self._r2.download(key)
        except Exception as exc:
            logger.warning("Download failed for %s: %s", key, exc)
            return None

    def _sync_collections(self) -> None:
        local_colls = {c.name for c in self._coll_repo.list_all()}
        for name, info in self._manifest.collections.items():
            if name not in local_colls:
                self._coll_repo.create(name, info.get("description", ""))

    def _insert_pulled_document(self, doc_id: str, data: dict) -> None:
        meta = data["metadata"]
        vectors = data["vectors"]

        collection_id = None
        if meta.get("collection_name"):
            colls = self._coll_repo.list_all()
            for c in colls:
                if c.name == meta["collection_name"]:
                    collection_id = c.id
                    break

        sync_source_path = f"sync://{doc_id}"
        doc = self._doc_repo.create(
            title=meta["title"],
            source_type=meta["source_type"],
            source_path=sync_source_path,
            collection_id=collection_id,
            token_count=meta.get("token_count", 0),
        )

        try:
            if vectors.get("ids"):
                chroma_coll = self._chroma.get_or_create_collection("default")
                remapped_metadatas = []
                for m in vectors.get("metadatas", []):
                    rm = dict(m)
                    rm["source"] = sync_source_path
                    remapped_metadatas.append(rm)

                chroma_coll.upsert(
                    ids=vectors["ids"],
                    embeddings=vectors.get("embeddings"),
                    metadatas=remapped_metadatas,
                    documents=vectors.get("documents"),
                )

            if self._tag_repo and meta.get("tags"):
                for tag_name in meta["tags"]:
                    self._tag_repo.add_tag_to_document(doc.id, tag_name)

        except Exception:
            self._doc_repo.delete(doc.id)
            raise
