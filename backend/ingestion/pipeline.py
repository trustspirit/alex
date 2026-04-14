from __future__ import annotations

import logging
import threading
from typing import Callable

from backend.ingestion.loaders.pdf_loader import PdfLoader
from backend.ingestion.loaders.youtube_loader import YoutubeLoader
from backend.ingestion.loaders.markdown_loader import MarkdownLoader
from backend.ingestion.loaders.text_loader import TextLoader
from backend.ingestion.chunker import Chunker
from backend.ingestion.summarizer import Summarizer
from backend.ingestion.metadata_extractor import extract_metadata

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Orchestrates the full ingestion flow: load → chunk → summarize → index."""

    def __init__(
        self,
        document_repo,
        index_manager,
        llm,
        embed_model,
        settings_repo,
        on_progress: Callable | None = None,  # (doc_id, step, percent) -> None
        on_warning: Callable | None = None,   # (doc_id, warning) -> None
    ) -> None:
        self._doc_repo = document_repo
        self._index_manager = index_manager
        self._llm = llm
        self._embed_model = embed_model
        self._settings_repo = settings_repo
        self._on_progress = on_progress
        self._on_warning = on_warning
        self._chunker = Chunker()
        self._summarizer = Summarizer(llm=llm)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ingest(
        self,
        source_path: str,
        source_type: str,
        collection_id: int | None = None,
        tags: list | None = None,
    ) -> dict:
        """Synchronous ingestion flow.

        Returns
        -------
        dict
            ``{"doc_id": int, "error": str | None, "token_count": int}``
        """
        # Step 1: Create document record (status: pending)
        doc = self._doc_repo.create(
            title="",
            source_type=source_type,
            source_path=source_path,
            collection_id=collection_id,
        )
        doc_id: int = doc.id

        try:
            # Step 2: Update status to "processing", emit progress(10, "extracting")
            self._doc_repo.update_status(doc_id, "processing")
            self._emit_progress(doc_id, "extracting", 10)

            # Step 3: Load document using appropriate loader
            load_result = self._load(source_path, source_type)

            # Step 4: If fallback used, call set_fallback and emit warning
            if load_result.fallback_used:
                self._doc_repo.set_fallback(doc_id, load_result.fallback_warning)
                self._emit_warning(doc_id, load_result.fallback_warning)

            # Step 5: Extract metadata (title, token_count), update doc
            metadata = extract_metadata(load_result.documents, source_path, source_type)
            title = metadata.get("title", "")
            token_count = metadata.get("token_count", 0)

            # Update title and token_count on doc
            self._doc_repo.update_title(doc_id, title)
            self._doc_repo.set_token_count(doc_id, token_count)

            # Step 6: Chunking
            self._emit_progress(doc_id, "chunking", 30)
            nodes = self._chunker.chunk(
                load_result.documents,
                has_structure=load_result.has_structure,
                embed_model=self._embed_model,
            )

            # Step 7: Summarizing
            self._emit_progress(doc_id, "summarizing", 50)
            full_text = "\n".join(doc_obj.text for doc_obj in load_result.documents)
            self._summarizer.summarize_document(full_text)
            if nodes:
                self._summarizer.summarize_chunks(nodes)

            # Step 7b: Generate QA pairs and add as extra nodes
            if self._llm and nodes:
                try:
                    qa_pairs = self._summarizer.generate_qa_pairs(full_text[:4000])
                    for qa in qa_pairs:
                        qa_text = f"Q: {qa['question']}\nA: {qa['answer']}"
                        qa_node = type(nodes[0])(text=qa_text, metadata={"type": "qa_pair", "source": source_path})
                        nodes.append(qa_node)
                except Exception as exc:
                    logger.warning("QA pair generation failed: %s", exc)

            # Step 8: Indexing
            self._emit_progress(doc_id, "indexing", 70)
            if nodes:
                self._index_manager.build_vector_index(nodes)

            # Step 9: Complete
            self._emit_progress(doc_id, "completed", 100)
            self._doc_repo.update_status(doc_id, "completed")

            return {"doc_id": doc_id, "error": None, "token_count": token_count}

        except Exception as exc:
            logger.error("Ingestion failed for doc %s: %s", doc_id, exc)
            self._doc_repo.update_status(doc_id, "failed")
            return {"doc_id": doc_id, "error": str(exc), "token_count": 0}

    def ingest_async(
        self,
        source_path: str,
        source_type: str,
        collection_id: int | None = None,
        tags: list | None = None,
        on_progress: Callable | None = None,
        on_warning: Callable | None = None,
        on_error: Callable | None = None,
    ) -> int:
        """Start ingestion in a background thread and return doc_id immediately.

        Returns
        -------
        int
            The doc_id created for this ingestion job.
        """
        # Create document record synchronously so we can return the id right away.
        # Use filename as initial title so it's never blank.
        from pathlib import Path
        initial_title = Path(source_path).stem.replace("_", " ").replace("-", " ").title()
        if source_type == "youtube":
            initial_title = source_path  # Show URL as title until metadata is extracted

        doc = self._doc_repo.create(
            title=initial_title,
            source_type=source_type,
            source_path=source_path,
            collection_id=collection_id,
        )
        doc_id: int = doc.id

        thread = threading.Thread(
            target=self._run_ingestion,
            args=(doc_id, source_path, source_type, collection_id, tags,
                  on_progress, on_warning, on_error),
            daemon=True,
        )
        thread.start()

        return doc_id

    def reingest_async(
        self,
        doc_id: int,
        source_path: str,
        source_type: str,
        collection_id: int | None = None,
        on_progress: Callable | None = None,
        on_warning: Callable | None = None,
    ) -> None:
        """Re-ingest an existing document (doc already exists in DB)."""
        thread = threading.Thread(
            target=self._run_ingestion,
            args=(doc_id, source_path, source_type, collection_id, None),
            kwargs={"on_progress": on_progress, "on_warning": on_warning},
            daemon=True,
        )
        thread.start()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _run_ingestion(
        self,
        doc_id: int,
        source_path: str,
        source_type: str,
        collection_id: int | None,
        tags: list | None,
        on_progress: Callable | None = None,
        on_warning: Callable | None = None,
        on_error: Callable | None = None,
    ) -> None:
        """Background-thread ingestion body (doc already created)."""
        logger.info("_run_ingestion started: doc_id=%s path=%s type=%s", doc_id, source_path, source_type)
        # Use per-invocation callbacks if provided, else fall back to instance-level
        progress_cb = on_progress or self._on_progress
        warning_cb = on_warning or self._on_warning
        error_cb = on_error

        try:
            self._doc_repo.update_status(doc_id, "processing")
            self._emit_progress(doc_id, "extracting", 10, progress_cb)
            logger.info("[doc %s] Step 1/5: Extracting text...", doc_id)

            load_result = self._load(source_path, source_type)
            logger.info("[doc %s] Extraction done. %d documents, fallback=%s",
                        doc_id, len(load_result.documents), load_result.fallback_used)

            if not load_result.documents:
                raise RuntimeError("No text could be extracted from the document. The file may be image-only or corrupted.")

            if load_result.fallback_used:
                self._doc_repo.set_fallback(doc_id, load_result.fallback_warning)
                self._emit_warning(doc_id, load_result.fallback_warning, warning_cb)

            metadata = extract_metadata(load_result.documents, source_path, source_type)
            token_count = metadata.get("token_count", 0)
            self._doc_repo.set_token_count(doc_id, token_count)
            logger.info("[doc %s] Metadata: title=%s tokens=%d", doc_id, metadata.get("title"), token_count)

            title = metadata.get("title", "")
            if title:
                self._doc_repo.update_title(doc_id, title)

            self._emit_progress(doc_id, "chunking", 30, progress_cb)
            logger.info("[doc %s] Step 2/5: Chunking...", doc_id)
            nodes = self._chunker.chunk(
                load_result.documents,
                has_structure=load_result.has_structure,
                embed_model=self._embed_model,
            )
            logger.info("[doc %s] Chunking done. %d nodes", doc_id, len(nodes))

            self._emit_progress(doc_id, "summarizing", 50, progress_cb)
            logger.info("[doc %s] Step 3/5: Summarizing...", doc_id)
            full_text = "\n".join(doc_obj.text for doc_obj in load_result.documents)
            if self._llm:
                self._summarizer.summarize_document(full_text)
                # Skip per-chunk summarization — too many LLM calls for large docs.
                # The vector index handles retrieval without chunk summaries.
                logger.info("[doc %s] Document summary generated. Skipping per-chunk summaries (%d nodes).", doc_id, len(nodes))
            else:
                logger.info("[doc %s] Skipping summarization (no LLM configured)", doc_id)
            logger.info("[doc %s] Summarization done.", doc_id)

            # Generate QA pairs (only from first portion of text, single LLM call)
            if self._llm and nodes:
                try:
                    logger.info("[doc %s] Generating QA pairs...", doc_id)
                    qa_pairs = self._summarizer.generate_qa_pairs(full_text[:4000])
                    for qa in qa_pairs:
                        qa_text = f"Q: {qa['question']}\nA: {qa['answer']}"
                        qa_node = type(nodes[0])(text=qa_text, metadata={"type": "qa_pair", "source": source_path})
                        nodes.append(qa_node)
                    logger.info("[doc %s] QA pairs added: %d", doc_id, len(qa_pairs))
                except Exception as exc:
                    logger.warning("[doc %s] QA pair generation failed: %s", doc_id, exc)

            self._emit_progress(doc_id, "indexing", 70, progress_cb)
            logger.info("[doc %s] Step 4/5: Indexing %d nodes...", doc_id, len(nodes))
            if nodes:
                self._index_manager.build_vector_index(nodes)
            logger.info("[doc %s] Indexing done.", doc_id)

            self._emit_progress(doc_id, "completed", 100, progress_cb)
            self._doc_repo.update_status(doc_id, "completed")
            logger.info("[doc %s] Step 5/5: COMPLETED successfully.", doc_id)

        except Exception as exc:
            logger.error("Async ingestion failed for doc %s: %s", doc_id, exc, exc_info=True)
            try:
                self._doc_repo.update_status(doc_id, "failed")
                self._doc_repo.set_fallback(
                    doc_id, f"Processing failed: {exc}"
                )
            except Exception:
                logger.error("Could not update failed status for doc %s", doc_id)
            # Push error to frontend
            if error_cb:
                try:
                    error_cb(doc_id, str(exc))
                except Exception:
                    pass

    def _load(self, source_path: str, source_type: str):
        """Route source_path to the correct loader based on source_type."""
        if source_type == "pdf":
            api_key = self._settings_repo.get_secret("llamaparse_api_key") or ""
            loader = PdfLoader(llamaparse_api_key=api_key)
            return loader.load(source_path)
        elif source_type == "youtube":
            openai_api_key = self._settings_repo.get_secret("openai_api_key") or ""
            loader = YoutubeLoader(openai_api_key=openai_api_key)
            return loader.load(source_path)
        elif source_type == "md":
            loader = MarkdownLoader()
            return loader.load(source_path)
        elif source_type == "txt":
            loader = TextLoader()
            return loader.load(source_path)
        else:
            raise ValueError(f"Unsupported source_type: '{source_type}'")

    def _emit_progress(self, doc_id: int, step: str, percent: int,
                        callback: Callable | None = None) -> None:
        cb = callback or self._on_progress
        if cb is not None:
            try:
                cb(doc_id, step, percent)
            except Exception as exc:
                logger.warning("on_progress callback raised: %s", exc)

    def _emit_warning(self, doc_id: int, warning: str | None,
                       callback: Callable | None = None) -> None:
        cb = callback or self._on_warning
        if cb is not None and warning is not None:
            try:
                cb(doc_id, warning)
            except Exception as exc:
                logger.warning("on_warning callback raised: %s", exc)
