from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class SourceTracker:
    """Extract, format, and serialise source citations from LlamaIndex responses."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(self, response) -> list[dict]:
        """Extract source information from a LlamaIndex response object.

        Each element of ``response.source_nodes`` is a ``NodeWithScore`` whose
        ``.node.metadata`` dict contains at minimum ``"source"`` and ``"type"``
        keys, and optionally ``"page"`` and ``"fallback"``.

        Parameters
        ----------
        response:
            A LlamaIndex query response with a ``source_nodes`` attribute.

        Returns
        -------
        list[dict]
            One dict per source node with keys:
            ``source``, ``type``, ``page``, ``score``, ``fallback``.
        """
        raw: list[dict] = []
        for node_with_score in response.source_nodes:
            metadata = node_with_score.node.metadata
            page = (
                metadata.get("page_label")
                or metadata.get("page")
                or metadata.get("page_number")
            )
            # Include a text preview (first 300 chars)
            text = getattr(node_with_score.node, "text", "") or ""
            preview = text[:300].strip()
            if len(text) > 300:
                preview += "..."

            raw.append(
                {
                    "source": metadata.get("source", ""),
                    "type": metadata.get("type", ""),
                    "page": page,
                    "score": node_with_score.score,
                    "fallback": bool(metadata.get("fallback", False)),
                    "preview": preview,
                }
            )

        # Group by source file, collect unique pages with best scores
        grouped: dict[str, dict] = {}
        for s in raw:
            src = s["source"]
            if src not in grouped:
                grouped[src] = {
                    "source": src,
                    "type": s["type"],
                    "fallback": s["fallback"],
                    "pages": [],
                }
            # Add page if not already present
            page_entry = {"page": s["page"], "score": s["score"], "preview": s["preview"]}
            existing_pages = [p["page"] for p in grouped[src]["pages"]]
            if s["page"] not in existing_pages:
                grouped[src]["pages"].append(page_entry)
            else:
                # Keep higher score for same page
                for p in grouped[src]["pages"]:
                    if p["page"] == s["page"] and (s["score"] or 0) > (p["score"] or 0):
                        p["score"] = s["score"]
                        p["preview"] = s["preview"]

        # Sort pages by score desc within each group
        sources = []
        for g in grouped.values():
            g["pages"].sort(key=lambda p: p["score"] or 0, reverse=True)
            g["best_score"] = g["pages"][0]["score"] if g["pages"] else None
            sources.append(g)

        sources.sort(key=lambda s: s["best_score"] or 0, reverse=True)
        logger.debug("Extracted %d raw sources → %d grouped sources.", len(raw), len(sources))
        return sources

    def format_for_display(self, sources: list[dict]) -> list[dict]:
        """Format source dicts for frontend consumption.

        Parameters
        ----------
        sources:
            List of source dicts as returned by :meth:`extract`.

        Returns
        -------
        list[dict]
            Each dict has keys:
            ``display_name``, ``detail``, ``score``, ``has_warning``.
        """
        formatted: list[dict] = []
        for src in sources:
            source_path: str = src.get("source", "")
            source_type: str = src.get("type", "")
            page = src.get("page")
            score = src.get("score")
            fallback: bool = bool(src.get("fallback", False))

            # display_name: filename for file-based sources, full URL for YouTube
            if source_type == "youtube":
                display_name = source_path
            else:
                display_name = Path(source_path).name if source_path else source_path

            # detail string
            parts: list[str] = []
            if page is not None:
                parts.append(f"p.{page}")
            if score is not None:
                parts.append(f"score: {score:.2f}")
            detail = ", ".join(parts)

            formatted.append(
                {
                    "display_name": display_name,
                    "detail": detail,
                    "score": score,
                    "has_warning": fallback,
                }
            )
        return formatted

    def to_json(self, sources: list[dict]) -> str:
        """Serialise a list of source dicts to a JSON string.

        Parameters
        ----------
        sources:
            List of source dicts (as returned by :meth:`extract`).

        Returns
        -------
        str
            JSON-encoded string representation.
        """
        return json.dumps(sources)
