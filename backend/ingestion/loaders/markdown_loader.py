from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional imports – wrap in try/except so missing libraries don't crash
# at import time.  Imported at module level so tests can patch them.
# ---------------------------------------------------------------------------

try:
    from llama_index.core import Document
except Exception:
    # Minimal stand-in when llama_index is not installed
    class Document:  # type: ignore[no-redef]
        def __init__(self, text: str = "", metadata: dict | None = None) -> None:
            self.text = text
            self.metadata: dict = metadata or {}


try:
    from llama_index.readers.file import MarkdownReader
except Exception:
    MarkdownReader = None  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# LoadResult
# ---------------------------------------------------------------------------

@dataclass
class LoadResult:
    documents: list
    fallback_used: bool = False
    fallback_warning: str | None = None
    has_structure: bool = True  # Markdown can have structure (headings)


# ---------------------------------------------------------------------------
# MarkdownLoader
# ---------------------------------------------------------------------------

class MarkdownLoader:
    """Load Markdown files with structure detection."""

    def load(self, file_path: str) -> LoadResult:
        """Load *file_path* and create Document(s).

        Tries to use llama_index.readers.file.MarkdownReader if available.
        Falls back to simple file reading if not.

        Returns a LoadResult with has_structure based on presence of markdown headings.
        """
        # --- Try MarkdownReader from llama_index ---
        if MarkdownReader is not None:
            try:
                reader = MarkdownReader()
                documents = reader.load_data(file_path)
                has_structure = self._detect_structure(documents)
                logger.debug("MarkdownReader succeeded for %s", file_path)
                return LoadResult(
                    documents=documents,
                    fallback_used=False,
                    fallback_warning=None,
                    has_structure=has_structure,
                )
            except Exception as exc:
                logger.warning("MarkdownReader failed (%s), falling back to manual read…", exc)

        # --- Fallback: read file manually ---
        try:
            content = Path(file_path).read_text(encoding="utf-8")
            doc = Document(
                text=content,
                metadata={
                    "source": file_path,
                    "type": "markdown",
                },
            )
            has_structure = self._detect_structure([doc])
            logger.debug("Manual markdown read succeeded for %s", file_path)
            return LoadResult(
                documents=[doc],
                fallback_used=False,
                fallback_warning=None,
                has_structure=has_structure,
            )
        except Exception as exc:
            logger.error("Failed to load markdown file (%s).", exc)
            raise RuntimeError(
                f"마크다운 파일을 로드할 수 없습니다: {file_path}. "
                f"오류: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _detect_structure(self, documents: list) -> bool:
        """Check if markdown documents contain heading markers."""
        for doc in documents:
            if "# " in doc.text or "## " in doc.text:
                return True
        return False
