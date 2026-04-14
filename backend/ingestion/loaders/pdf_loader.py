from __future__ import annotations

import logging

from backend.ingestion.loaders.base import LoadResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional imports – wrap each in try/except so missing libraries don't crash
# at import time.  We import at module level so tests can easily patch them.
# ---------------------------------------------------------------------------

try:
    from llama_cloud import LlamaParse
except Exception:  # ImportError or any install-time error
    LlamaParse = None  # type: ignore[assignment,misc]

try:
    from liteparse import LiteParser
except Exception:
    LiteParser = None  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# Internal helper for OpenDataLoader (import is attempted at call-time so the
# function itself is patchable in tests)
# ---------------------------------------------------------------------------

def _try_opendataloader(file_path: str) -> list:
    """Attempt to load *file_path* using OpenDataLoader.

    Raises an exception if the library is not installed or if loading fails.
    """
    try:
        import opendataloader  # type: ignore[import]
        loader = opendataloader.OpenDataLoader()
        return loader.load_data(file_path)
    except ImportError as exc:
        raise ImportError("opendataloader is not installed") from exc


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
            raise ImportError("llama_cloud is not installed")
        parser = LlamaParse(
            api_key=self._llamaparse_api_key,
            result_type="markdown",
            skip_diagonal_text=True,
        )
        return parser.load_data(file_path)

    def _load_liteparse(self, file_path: str) -> list:
        if LiteParser is None:
            raise ImportError("liteparse is not installed")
        parser = LiteParser()
        return parser.load_data(file_path)

    def _detect_structure(self, documents: list) -> bool:
        """Check if parsed markdown contains heading markers."""
        for doc in documents:
            if "##" in doc.text or "# " in doc.text:
                return True
        return False
