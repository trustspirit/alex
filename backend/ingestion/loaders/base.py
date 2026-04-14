from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LoadResult:
    documents: list
    fallback_used: bool = False
    fallback_warning: str | None = None
    has_structure: bool = True
