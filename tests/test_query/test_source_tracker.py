from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from backend.query.source_tracker import SourceTracker


def _make_node_with_score(
    source: str = "/docs/file.pdf",
    source_type: str = "pdf",
    page: int | None = 3,
    score: float = 0.92,
    fallback: bool = False,
) -> MagicMock:
    """Build a mock LlamaIndex NodeWithScore."""
    node = MagicMock()
    node.node.metadata = {
        "source": source,
        "type": source_type,
    }
    if page is not None:
        node.node.metadata["page"] = page
    node.score = score
    node.node.metadata["fallback"] = fallback
    return node


class TestSourceTrackerExtract:
    """Tests for SourceTracker.extract()."""

    def test_extract_two_nodes(self):
        """extract() returns one dict per source_node."""
        tracker = SourceTracker()

        pdf_node = _make_node_with_score(
            source="/docs/paper.pdf", source_type="pdf", page=5, score=0.95
        )
        yt_node = _make_node_with_score(
            source="https://youtu.be/abc123", source_type="youtube", page=None, score=0.78
        )

        mock_response = MagicMock()
        mock_response.source_nodes = [pdf_node, yt_node]

        sources = tracker.extract(mock_response)

        assert len(sources) == 2
        assert sources[0]["source"] == "/docs/paper.pdf"
        assert sources[0]["type"] == "pdf"
        assert sources[0]["page"] == 5
        assert sources[0]["score"] == 0.95
        assert sources[0]["fallback"] is False

        assert sources[1]["source"] == "https://youtu.be/abc123"
        assert sources[1]["type"] == "youtube"
        assert sources[1]["page"] is None
        assert sources[1]["score"] == 0.78

    def test_extract_empty_source_nodes(self):
        """extract() returns empty list when there are no source nodes."""
        tracker = SourceTracker()
        mock_response = MagicMock()
        mock_response.source_nodes = []
        assert tracker.extract(mock_response) == []

    def test_extract_fallback_flag(self):
        """extract() captures fallback=True from metadata."""
        tracker = SourceTracker()
        node = _make_node_with_score(fallback=True, score=0.50)
        mock_response = MagicMock()
        mock_response.source_nodes = [node]
        sources = tracker.extract(mock_response)
        assert sources[0]["fallback"] is True


class TestSourceTrackerFormatForDisplay:
    """Tests for SourceTracker.format_for_display()."""

    def test_pdf_source_shows_filename_and_page(self):
        """PDF sources show the filename and page number."""
        tracker = SourceTracker()
        sources = [
            {"source": "/some/path/report.pdf", "type": "pdf", "page": 3, "score": 0.92, "fallback": False}
        ]
        formatted = tracker.format_for_display(sources)
        assert len(formatted) == 1
        item = formatted[0]
        assert item["display_name"] == "report.pdf"
        assert "p.3" in item["detail"]
        assert "0.92" in item["detail"]
        assert item["has_warning"] is False
        assert "score" in item

    def test_youtube_source_shows_full_url(self):
        """YouTube sources show the full URL as display_name."""
        tracker = SourceTracker()
        sources = [
            {"source": "https://youtu.be/abc123", "type": "youtube", "page": None, "score": 0.78, "fallback": False}
        ]
        formatted = tracker.format_for_display(sources)
        item = formatted[0]
        assert item["display_name"] == "https://youtu.be/abc123"
        assert item["has_warning"] is False

    def test_fallback_shows_warning(self):
        """Sources with fallback=True get has_warning=True."""
        tracker = SourceTracker()
        sources = [
            {"source": "/docs/file.txt", "type": "text", "page": None, "score": 0.50, "fallback": True}
        ]
        formatted = tracker.format_for_display(sources)
        assert formatted[0]["has_warning"] is True

    def test_format_empty_list(self):
        """format_for_display([]) returns []."""
        tracker = SourceTracker()
        assert tracker.format_for_display([]) == []


class TestSourceTrackerToJson:
    """Tests for SourceTracker.to_json()."""

    def test_to_json_valid_json(self):
        """to_json() returns a valid JSON string."""
        tracker = SourceTracker()
        sources = [
            {"source": "/docs/a.pdf", "type": "pdf", "page": 1, "score": 0.9, "fallback": False}
        ]
        result = tracker.to_json(sources)
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert parsed[0]["source"] == "/docs/a.pdf"

    def test_to_json_empty_list(self):
        """to_json([]) returns '[]'."""
        tracker = SourceTracker()
        assert tracker.to_json([]) == "[]"
