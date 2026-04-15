from __future__ import annotations

import logging

from backend.ingestion.loaders.base import LoadResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional imports – wrap each in try/except so missing libraries don't crash
# at import time.  We import at module level so tests can easily patch them.
# ---------------------------------------------------------------------------

try:
    from llama_cloud import LlamaCloud as _LlamaCloud
except Exception:
    _LlamaCloud = None  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# Internal helper for OpenDataLoader (import is attempted at call-time so the
# function itself is patchable in tests)
# ---------------------------------------------------------------------------

def _try_opendataloader(file_path: str) -> list:
    """Attempt to load *file_path* using OpenDataLoader PDF.

    Converts the PDF to markdown via ``opendataloader_pdf.convert`` and wraps
    the result in Document objects.

    Raises an exception if the library is not installed or if loading fails.
    """
    try:
        import opendataloader_pdf  # type: ignore[import]
        import tempfile
        from backend.ingestion.loaders.document import Document

        with tempfile.TemporaryDirectory() as tmp_dir:
            opendataloader_pdf.convert(
                input_path=[file_path],
                output_dir=tmp_dir,
                format="markdown",
            )
            # Read the generated markdown file
            from pathlib import Path
            md_files = list(Path(tmp_dir).glob("*.md"))
            documents = []
            for md_file in md_files:
                text = md_file.read_text(encoding="utf-8")
                documents.append(Document(
                    text=text,
                    metadata={"source": file_path, "type": "pdf", "method": "opendataloader"},
                ))
            if not documents:
                raise RuntimeError("OpenDataLoader produced no output")
            return documents
    except ImportError as exc:
        raise ImportError("opendataloader-pdf is not installed") from exc


# ---------------------------------------------------------------------------
# PdfLoader
# ---------------------------------------------------------------------------

class PdfLoader:
    """3-tier PDF loader: LlamaParse v2 → MinerU → OpenDataLoader."""

    def __init__(self, llamaparse_api_key: str = "") -> None:
        self._llamaparse_api_key = llamaparse_api_key

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, file_path: str) -> LoadResult:
        """Load *file_path* using the best available parser.

        Tries tiers in order:
        1. LlamaParse v2  (cloud, highest quality)
        2. MinerU         (local AI)
        3. OpenDataLoader (local, rule-based)

        Raises RuntimeError when all tiers fail.
        """
        # --- Tier 1: LlamaParse ---
        try:
            documents = self._load_llamaparse(file_path)
            logger.debug("LlamaParse succeeded for %s", file_path)
            return LoadResult(
                documents=documents,
                fallback_used=False,
                fallback_warning=None,
                has_structure=self._detect_structure(documents),
            )
        except Exception as exc:
            logger.warning("LlamaParse failed (%s), trying MinerU…", exc)

        # --- Tier 2: MinerU ---
        try:
            documents = self._load_mineru(file_path)
            warning = (
                "클라우드 파싱 서비스에 연결할 수 없어 MinerU(로컬 AI)로 처리했습니다. "
                "대부분의 문서는 동등한 품질로 처리됩니다."
            )
            logger.info("MinerU succeeded for %s", file_path)
            return LoadResult(
                documents=documents,
                fallback_used=True,
                fallback_warning=warning,
                has_structure=self._detect_structure(documents),
            )
        except Exception as exc:
            if "model" in str(exc).lower() or "weight" in str(exc).lower():
                logger.warning(
                    "MinerU models not found. Run 'mineru-models download' to install. "
                    "Falling back to OpenDataLoader."
                )
            else:
                logger.warning("MinerU failed (%s), trying OpenDataLoader…", exc)

        # --- Tier 3: OpenDataLoader ---
        try:
            documents = _try_opendataloader(file_path)
            warning = (
                "AI 파서를 사용할 수 없어 OpenDataLoader(규칙 기반)로 처리했습니다. "
                "복잡한 레이아웃에서 정확도가 낮을 수 있습니다."
            )
            logger.warning(warning)
            return LoadResult(
                documents=documents,
                fallback_used=True,
                fallback_warning=warning,
                has_structure=self._detect_structure(documents),
            )
        except Exception as exc:
            logger.error("OpenDataLoader also failed (%s).", exc)

        raise RuntimeError(
            f"모든 PDF 파서가 실패했습니다: {file_path}. "
            "LlamaParse, MinerU, OpenDataLoader 모두 사용할 수 없습니다."
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_llamaparse(self, file_path: str) -> list:
        if _LlamaCloud is None:
            raise ImportError("llama-cloud SDK is not installed")
        if not self._llamaparse_api_key:
            raise ValueError("LlamaParse API key is not configured")
        from backend.ingestion.loaders.document import Document

        client = _LlamaCloud(api_key=self._llamaparse_api_key)
        result = client.parsing.parse(
            tier="agentic",
            version="latest",
            upload_file=open(file_path, "rb"),
            expand=["markdown"],
        )

        documents = []
        if result.markdown and result.markdown.pages:
            for page in result.markdown.pages:
                text = page.markdown or ""
                if not text.strip():
                    continue
                documents.append(Document(
                    text=text,
                    metadata={
                        "source": file_path,
                        "type": "pdf",
                        "method": "llamaparse",
                        "page_label": str(page.page_number),
                    },
                ))

        if not documents:
            raise RuntimeError("LlamaParse returned empty result")
        return documents

    def _load_mineru(self, file_path: str) -> list:
        """Tier 2: MinerU local AI parser."""
        import json
        import os
        import tempfile
        from pathlib import Path

        try:
            from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
            from magic_pdf.data.dataset import PymuDocDataset
            from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
            from magic_pdf.config.enums import SupportedPdfParseMethod
        except ImportError:
            raise ImportError(
                "magic-pdf is not installed. Run: pip install 'magic-pdf[full]'"
            )

        from backend.ingestion.loaders.document import Document

        reader = FileBasedDataReader("")
        pdf_bytes = reader.read(file_path)
        ds = PymuDocDataset(pdf_bytes)

        with tempfile.TemporaryDirectory() as tmp_dir:
            image_writer = FileBasedDataWriter(os.path.join(tmp_dir, "images"))

            if ds.classify() == SupportedPdfParseMethod.OCR:
                infer_result = ds.apply(doc_analyze, ocr=True)
                pipe_result = infer_result.pipe_ocr_mode(image_writer)
            else:
                infer_result = ds.apply(doc_analyze, ocr=False)
                pipe_result = infer_result.pipe_txt_mode(image_writer)

            # Try API method first, fall back to file-based
            content_list = None
            markdown = None
            try:
                content_list = pipe_result.get_content_list()
                markdown = pipe_result.get_markdown(image_dir="images")
            except AttributeError:
                # File-based fallback
                cl_files = list(Path(tmp_dir).glob("*_content_list*.json"))
                md_files = list(Path(tmp_dir).glob("*.md"))
                if cl_files:
                    content_list = json.loads(cl_files[0].read_text(encoding="utf-8"))
                if md_files:
                    markdown = md_files[0].read_text(encoding="utf-8")

            # Build page-level documents from content_list
            documents = self._build_page_documents(content_list, markdown, file_path)

        if not documents:
            raise RuntimeError("MinerU produced no output")
        return documents

    def _build_page_documents(self, content_list, markdown, file_path):
        """Build page-level Document list from MinerU content_list."""
        from collections import defaultdict
        from backend.ingestion.loaders.document import Document

        # Try page-level from content_list
        if content_list and isinstance(content_list, list):
            first = content_list[0] if content_list else {}
            if isinstance(first, dict) and "page_idx" in first:
                pages = defaultdict(list)
                for item in content_list:
                    page_idx = item.get("page_idx", 0)
                    text = item.get("text", "") or item.get("md", "") or ""
                    if text.strip():
                        pages[page_idx].append(text)

                documents = []
                for page_idx in sorted(pages.keys()):
                    page_text = "\n\n".join(pages[page_idx])
                    documents.append(Document(
                        text=page_text,
                        metadata={
                            "source": file_path,
                            "type": "pdf",
                            "method": "mineru",
                            "page_label": str(page_idx + 1),
                        },
                    ))
                if documents:
                    return documents

        # Fallback: whole markdown as single document
        if markdown and markdown.strip():
            return [Document(
                text=markdown,
                metadata={"source": file_path, "type": "pdf", "method": "mineru"},
            )]

        return []

    def _detect_structure(self, documents: list) -> bool:
        """Check if parsed markdown contains heading markers."""
        for doc in documents:
            if "##" in doc.text or "# " in doc.text:
                return True
        return False
