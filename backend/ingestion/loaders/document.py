from __future__ import annotations

try:
    from llama_index.core import Document
except ImportError:
    class Document:  # type: ignore[no-redef]
        def __init__(self, text: str = "", metadata: dict | None = None) -> None:
            self.text = text
            self.metadata: dict = metadata or {}
