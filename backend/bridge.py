from __future__ import annotations

import json
import logging
import threading
import time

try:
    import webview
except ImportError:  # pragma: no cover
    webview = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class BridgeAPI:
    """Exposes Python functionality to JavaScript via pywebview.

    All public methods are callable from JS as
    ``window.pywebview.api.<method>()``.
    """

    def __init__(
        self,
        pipeline,
        query_engine,
        document_repo,
        collection_repo,
        chat_repo,
        settings_repo,
        provider_manager,
        tag_repo=None,
        chroma_store=None,
    ) -> None:
        self._pipeline = pipeline
        self._query_engine = query_engine
        self._document_repo = document_repo
        self._collection_repo = collection_repo
        self._chat_repo = chat_repo
        self._settings_repo = settings_repo
        self._provider_manager = provider_manager
        self._tag_repo = tag_repo
        self._chroma_store = chroma_store
        self._window = None  # Set after window creation

    def set_window(self, window) -> None:
        self._window = window

    # ------------------------------------------------------------------
    # Internal JS push helper
    # ------------------------------------------------------------------

    def _push_js(self, callback_name: str, data: dict) -> None:
        """Serialize *data* and invoke the named JS bridge callback."""
        if self._window:
            json_data = json.dumps(data, ensure_ascii=False)
            self._window.evaluate_js(
                f"window.__bridge__ && window.__bridge__.{callback_name} && "
                f"window.__bridge__.{callback_name}({json_data})"
            )

    def _stream_response(
        self, session_id: int, answer: str, sources: list, mode: str
    ) -> None:
        """Push answer text in small chunks for streaming effect."""
        words = answer.split(' ')
        for i, word in enumerate(words):
            token = word if i == 0 else ' ' + word
            self._push_js("onToken", {"token": token})
            time.sleep(0.02)

        self._push_js("onQueryComplete", {
            "session_id": session_id,
            "answer": answer,
            "sources": sources,
            "mode": mode,
        })

    # ------------------------------------------------------------------
    # Chat API
    # ------------------------------------------------------------------

    def ask(
        self,
        question: str,
        session_id: int | None = None,
        collection_id: int | None = None,
    ) -> dict:
        """Submit a question; process in background and push result via JS callback.

        Returns immediately with ``{"session_id": id, "status": "processing"}``.
        """
        # Create session if none provided
        if session_id is None:
            session = self._chat_repo.create_session(title=question[:60])
            session_id = session.id
        else:
            session = self._chat_repo.get_session(session_id)
            if session is None:
                session = self._chat_repo.create_session(title=question[:60])
                session_id = session.id

        # Persist user message
        self._chat_repo.add_message(session_id=session_id, role="user", content=question)

        def _run() -> None:
            try:
                result = self._query_engine.query(
                    question, collection_id=collection_id
                )
                answer = result.get("answer", "")
                sources_json = result.get("sources_json", "[]")

                # Persist assistant message
                self._chat_repo.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=answer,
                    source_references=sources_json,
                )

                self._stream_response(
                    session_id=session_id,
                    answer=answer,
                    sources=result.get("sources", []),
                    mode=result.get("mode", ""),
                )
            except Exception as exc:
                logger.error("ask() background query failed: %s", exc)
                self._push_js(
                    "onQueryError",
                    {"session_id": session_id, "error": str(exc)},
                )

        threading.Thread(target=_run, daemon=True).start()
        return {"session_id": session_id, "status": "processing"}

    def get_chat_sessions(self) -> list[dict]:
        """Return list of chat sessions as JSON-serialisable dicts."""
        sessions = self._chat_repo.list_sessions()
        result = []
        for s in sessions:
            result.append(
                {
                    "id": s.id,
                    "title": s.title,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                }
            )
        return result

    def get_chat_messages(self, session_id: int) -> list[dict]:
        """Return all messages for *session_id* as JSON-serialisable dicts."""
        messages = self._chat_repo.get_messages(session_id)
        result = []
        for m in messages:
            # Parse stored JSON sources back into a list
            sources: list = []
            if m.source_references:
                try:
                    sources = json.loads(m.source_references)
                except (json.JSONDecodeError, TypeError):
                    sources = []

            result.append(
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "sources": sources,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
            )
        return result

    def delete_chat_session(self, session_id: int) -> dict:
        """Delete a chat session and all its messages."""
        self._chat_repo.delete_session(session_id)
        return {"success": True}

    # ------------------------------------------------------------------
    # Document API
    # ------------------------------------------------------------------

    def ingest_document_content(
        self,
        filename: str,
        base64_content: str,
        source_type: str,
        collection_id: int | None = None,
    ) -> dict:
        """Receive file content (base64) from drag & drop, save to temp, then ingest."""
        import base64
        import tempfile
        from pathlib import Path

        logger.info("ingest_document_content called: filename=%s type=%s", filename, source_type)
        try:
            # Decode and save to persistent temp location
            data = base64.b64decode(base64_content)
            upload_dir = Path.home() / ".alex" / "uploads"
            upload_dir.mkdir(parents=True, exist_ok=True)
            file_path = upload_dir / filename
            file_path.write_bytes(data)
            logger.info("Saved uploaded file to %s (%d bytes)", file_path, len(data))

            return self.ingest_document(str(file_path), source_type, collection_id)
        except Exception as exc:
            logger.error("ingest_document_content failed: %s", exc, exc_info=True)
            self._push_js("onIngestError", {"doc_id": -1, "error": str(exc)})
            return {"error": str(exc)}

    def ingest_document(
        self,
        source_path: str,
        source_type: str,
        collection_id: int | None = None,
    ) -> dict:
        """Start async document ingestion; push progress/warnings/errors via JS callbacks."""
        logger.info("ingest_document called: path=%s type=%s", source_path, source_type)

        def _on_progress(doc_id: int, step: str, percent: int) -> None:
            self._push_js(
                "onIngestProgress",
                {"doc_id": doc_id, "step": step, "percent": percent},
            )

        def _on_warning(doc_id: int, warning: str) -> None:
            self._push_js(
                "onIngestWarning",
                {"doc_id": doc_id, "warning": warning},
            )

        def _on_error(doc_id: int, error: str) -> None:
            self._push_js(
                "onIngestError",
                {"doc_id": doc_id, "error": error},
            )

        try:
            doc_id = self._pipeline.ingest_async(
                source_path=source_path,
                source_type=source_type,
                collection_id=collection_id,
                on_progress=_on_progress,
                on_warning=_on_warning,
                on_error=_on_error,
            )
            return {"doc_id": doc_id, "status": "processing"}
        except Exception as exc:
            logger.error("ingest_document failed synchronously: %s", exc, exc_info=True)
            self._push_js("onIngestError", {"doc_id": -1, "error": str(exc)})
            return {"error": str(exc)}

    def get_documents(self, collection_id: int | None = None) -> list[dict]:
        """Return documents, optionally filtered by *collection_id*."""
        if collection_id is not None:
            docs = self._document_repo.list_by_collection(collection_id)
        else:
            docs = self._document_repo.list_all()

        result = []
        for d in docs:
            result.append(
                {
                    "id": d.id,
                    "title": d.title,
                    "source_type": d.source_type,
                    "source_path": d.source_path,
                    "collection_id": d.collection_id,
                    "status": d.status,
                    "token_count": d.token_count,
                    "fallback_used": d.fallback_used,
                    "fallback_warning": d.fallback_warning,
                    "created_at": d.created_at.isoformat() if d.created_at else None,
                    "updated_at": d.updated_at.isoformat() if d.updated_at else None,
                    "tags": [{"id": t.id, "name": t.name} for t in (d.tags or [])],
                }
            )
        return result

    def delete_document(self, doc_id: int) -> dict:
        """Delete a document record and its associated vectors from ChromaDB."""
        doc = self._document_repo.get_by_id(doc_id)
        if doc and self._chroma_store:
            try:
                self._chroma_store.delete_documents_by_source("default", doc.source_path)
            except Exception as exc:
                logger.warning("Failed to delete vectors for doc %s: %s", doc_id, exc)
        self._document_repo.delete(doc_id)
        return {"success": True}

    def reindex_document(self, doc_id: int) -> dict:
        """Re-ingest an existing document."""
        doc = self._document_repo.get_by_id(doc_id)
        if not doc:
            return {"error": "Document not found"}

        # Reset and re-ingest
        self._document_repo.update_status(doc_id, "pending")

        def _on_progress(d_id, step, pct):
            self._push_js("onIngestProgress", {"doc_id": d_id, "step": step, "percent": pct})

        def _on_warning(d_id, warning):
            self._push_js("onIngestWarning", {"doc_id": d_id, "warning": warning})

        self._pipeline.reingest_async(
            doc_id, doc.source_path, doc.source_type, doc.collection_id,
            on_progress=_on_progress, on_warning=_on_warning,
        )
        return {"doc_id": doc_id, "status": "reindexing"}

    def move_document(self, doc_id: int, collection_id: int | None) -> dict:
        """Move a document to a different collection."""
        self._document_repo.move_to_collection(doc_id, collection_id)
        return {"success": True}

    # ------------------------------------------------------------------
    # Collection API
    # ------------------------------------------------------------------

    def get_collections(self) -> list[dict]:
        """Return all collections as JSON-serialisable dicts."""
        colls = self._collection_repo.list_all()
        return [
            {"id": c.id, "name": c.name, "description": c.description or ""}
            for c in colls
        ]

    def create_collection(self, name: str, description: str = "") -> dict:
        """Create a new collection and return its id and name."""
        coll = self._collection_repo.create(name=name, description=description)
        return {"id": coll.id, "name": coll.name}

    def rename_collection(self, coll_id: int, new_name: str) -> dict:
        """Rename an existing collection."""
        self._collection_repo.rename(coll_id, new_name)
        return {"success": True}

    def delete_collection(self, coll_id: int) -> dict:
        """Delete a collection."""
        self._collection_repo.delete(coll_id)
        return {"success": True}

    # ------------------------------------------------------------------
    # Settings API
    # ------------------------------------------------------------------

    def get_settings(self) -> list[dict]:
        """Return all settings as JSON-serialisable dicts."""
        settings = self._settings_repo.list_all()
        return [
            {
                "id": s.id,
                "key": s.key,
                "value": s.value,
                "encrypted": s.encrypted,
            }
            for s in settings
        ]

    def set_setting(self, key: str, value: str) -> dict:
        """Persist a plain (non-secret) setting."""
        self._settings_repo.set(key, value)
        return {"success": True}

    def set_api_key(self, provider: str, api_key: str) -> dict:
        """Store an API key in the system keyring under ``{provider}_api_key``."""
        self._settings_repo.set_secret(f"{provider}_api_key", api_key)
        return {"success": True}

    def get_providers(self) -> list[dict]:
        """Return available LLM providers with their model lists."""
        providers = self._provider_manager.list_providers()
        return [
            {
                "name": p.name,
                "display_name": p.display_name,
                "models": p.models,
                "embed_models": p.embed_models,
            }
            for p in providers
        ]

    # ------------------------------------------------------------------
    # File Dialog
    # ------------------------------------------------------------------

    def open_file_dialog(self) -> list[str] | None:
        """Open a native file picker and return selected paths, or None."""
        if self._window is None:
            return None
        try:
            paths = self._window.create_file_dialog(webview.OPEN_DIALOG if webview else 10)
            if paths:
                return list(paths)
            return None
        except Exception as exc:
            logger.warning("open_file_dialog failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Tag API
    # ------------------------------------------------------------------

    def get_tags(self) -> list[dict]:
        """Return all tags as JSON-serialisable dicts."""
        if not self._tag_repo:
            return []
        tags = self._tag_repo.list_all()
        return [{"id": t.id, "name": t.name} for t in tags]

    def add_tag_to_document(self, doc_id: int, tag_name: str) -> dict:
        """Add a tag to a document (creates the tag if needed)."""
        if self._tag_repo:
            self._tag_repo.add_tag_to_document(doc_id, tag_name)
        return {"success": True}

    def remove_tag_from_document(self, doc_id: int, tag_id: int) -> dict:
        """Remove a tag from a document."""
        if self._tag_repo:
            self._tag_repo.remove_tag_from_document(doc_id, tag_id)
        return {"success": True}

    # ------------------------------------------------------------------
    # Re-index all
    # ------------------------------------------------------------------

    def reindex_all_documents(self) -> dict:
        """Re-index all completed documents with new embedding model."""
        docs = self._document_repo.list_all()
        count = 0
        for doc in docs:
            if doc.status == "completed":
                self.reindex_document(doc.id)
                count += 1
        return {"count": count, "status": "reindexing"}

    # ------------------------------------------------------------------
    # Aliases for frontend compatibility
    # ------------------------------------------------------------------

    def list_sessions(self) -> list[dict]:
        return self.get_chat_sessions()

    def list_collections(self) -> list[dict]:
        return self.get_collections()

    def list_documents(self, collection_id: int | None = None) -> list[dict]:
        return self.get_documents(collection_id)

    def get_messages(self, session_id: int) -> list[dict]:
        return self.get_chat_messages(session_id)

    def create_session(self, title: str = "New Chat") -> dict:
        session = self._chat_repo.create_session(title=title)
        return {
            "id": session.id,
            "title": session.title,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        }

    def delete_session(self, session_id: int) -> dict:
        return self.delete_chat_session(session_id)
