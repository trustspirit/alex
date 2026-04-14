from __future__ import annotations

import logging

from backend.ingestion.loaders.base import LoadResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional imports – wrap each in try/except so missing libraries don't crash
# at import time.  We import at module level so tests can easily patch them.
# ---------------------------------------------------------------------------

try:
    from llama_parse import LlamaParse
except Exception:  # ImportError or any install-time error
    LlamaParse = None  # type: ignore[assignment,misc]

try:
    from liteparse import LiteParse as _LiteParse
except Exception:
    _LiteParse = None  # type: ignore[assignment,misc]


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
    """3-tier PDF loader: LlamaParse v2 → OpenDataLoader → LiteParse."""

    def __init__(self, llamaparse_api_key: str = "") -> None:
        self._llamaparse_api_key = llamaparse_api_key

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, file_path: str) -> LoadResult:
        """Load *file_path* using the best available parser.

        Tries tiers in order:
        1. LlamaParse v2  (cloud, highest quality)
        2. OpenDataLoader (local)
        3. LiteParse      (local, basic)

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
            logger.warning("LlamaParse failed (%s), trying OpenDataLoader…", exc)

        # --- Tier 2: OpenDataLoader ---
        try:
            documents = _try_opendataloader(file_path)
            warning = (
                "클라우드 파싱 서비스에 연결할 수 없어 OpenDataLoader(로컬)로 처리했습니다. "
                "대부분의 문서는 정상적으로 처리되나, 일부 복잡한 레이아웃에서 정확도가 다소 낮을 수 있습니다."
            )
            logger.warning(warning)
            return LoadResult(
                documents=documents,
                fallback_used=True,
                fallback_warning=warning,
                has_structure=self._detect_structure(documents),
            )
        except Exception as exc:
            logger.warning("OpenDataLoader failed (%s), trying LiteParse…", exc)

        # --- Tier 3: LiteParse ---
        try:
            documents = self._load_liteparse(file_path)
            warning = "로컬 기본 파서로 처리했습니다. 표나 복잡한 레이아웃의 정확도가 낮을 수 있습니다."
            logger.warning(warning)
            return LoadResult(
                documents=documents,
                fallback_used=True,
                fallback_warning=warning,
                has_structure=self._detect_structure(documents),
            )
        except Exception as exc:
            logger.error("LiteParse also failed (%s).", exc)

        raise RuntimeError(
            f"모든 PDF 파서가 실패했습니다: {file_path}. "
            "LlamaParse, OpenDataLoader, LiteParse 모두 사용할 수 없습니다."
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_llamaparse(self, file_path: str) -> list:
        if LlamaParse is None:
            raise ImportError("llama_parse is not installed")
        if not self._llamaparse_api_key:
            raise ValueError("LlamaParse API key is not configured")
        parser = LlamaParse(
            api_key=self._llamaparse_api_key,
            result_type="markdown",
            skip_diagonal_text=True,
        )
        docs = parser.load_data(file_path)
        if not docs:
            raise RuntimeError("LlamaParse returned empty result")
        return docs

    def _load_liteparse(self, file_path: str) -> list:
        if _LiteParse is None:
            raise ImportError("liteparse is not installed")
        from backend.ingestion.loaders.document import Document

        parser = _LiteParse()
        result = parser.parse(file_path)
        documents = []
        for page in range(result.num_pages):
            parsed_page = result.get_page(page)
            if parsed_page is None:
                continue
            text = parsed_page.text or ""
            if not text.strip():
                continue
            documents.append(Document(
                text=text,
                metadata={
                    "source": file_path,
                    "type": "pdf",
                    "method": "liteparse",
                    "page_label": str(page + 1),
                    },
                ))
        if not documents:
            raise RuntimeError("LiteParse produced no output")
        return documents

    def _detect_structure(self, documents: list) -> bool:
        """Check if parsed markdown contains heading markers."""
        for doc in documents:
            if "##" in doc.text or "# " in doc.text:
                return True
        return False
