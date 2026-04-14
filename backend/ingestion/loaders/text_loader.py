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


# ---------------------------------------------------------------------------
# LoadResult
# ---------------------------------------------------------------------------

@dataclass
class LoadResult:
    documents: list
    fallback_used: bool = False
    fallback_warning: str | None = None
    has_structure: bool = False  # Plain text is unstructured


# ---------------------------------------------------------------------------
# TextLoader
# ---------------------------------------------------------------------------

class TextLoader:
    """Load plain text files."""

    def load(self, file_path: str) -> LoadResult:
        """Load *file_path* as plain text and create a Document.

        Reads the file with UTF-8 encoding and creates a single Document.
        Plain text is always considered unstructured (has_structure=False).

        Returns a LoadResult with the document.
        """
        try:
            content = Path(file_path).read_text(encoding="utf-8")
            doc = Document(
                text=content,
                metadata={
                    "source": file_path,
                    "type": "text",
                },
            )
            logger.debug("Text file read succeeded for %s", file_path)
            return LoadResult(
                documents=[doc],
                fallback_used=False,
                fallback_warning=None,
                has_structure=False,
            )
        except Exception as exc:
            logger.error("Failed to load text file (%s).", exc)
            raise RuntimeError(
                f"텍스트 파일을 로드할 수 없습니다: {file_path}. "
                f"오류: {exc}"
            ) from exc
