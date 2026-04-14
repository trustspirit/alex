from __future__ import annotations

import logging
from pathlib import Path

from backend.ingestion.loaders.base import LoadResult
from backend.ingestion.loaders.document import Document

logger = logging.getLogger(__name__)


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
