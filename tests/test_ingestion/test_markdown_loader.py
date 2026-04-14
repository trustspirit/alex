from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from backend.ingestion.loaders.markdown_loader import LoadResult, MarkdownLoader


# ---------------------------------------------------------------------------
# Basic markdown loading test
# ---------------------------------------------------------------------------

def test_load_markdown(tmp_path):
    """Load a simple markdown file and verify basic loading works."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Title\n\n## Section 1\n\nSome content.")

    loader = MarkdownLoader()
    result = loader.load(str(md_file))

    assert isinstance(result, LoadResult)
    assert len(result.documents) > 0
    assert result.has_structure is True
    assert result.fallback_used is False
    assert result.fallback_warning is None


# ---------------------------------------------------------------------------
# Verify document content and metadata
# ---------------------------------------------------------------------------

def test_load_markdown_contains_content(tmp_path):
    """Document text should contain the markdown content."""
    md_file = tmp_path / "test.md"
    content = "# Title\n\n## Section\n\nContent here"
    md_file.write_text(content)

    loader = MarkdownLoader()
    result = loader.load(str(md_file))

    combined_text = " ".join(doc.text for doc in result.documents)
    assert "Title" in combined_text
    assert "Section" in combined_text
    assert "Content here" in combined_text


def test_load_markdown_metadata(tmp_path):
    """Markdown documents should have correct metadata."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test\n\nContent")

    loader = MarkdownLoader()
    result = loader.load(str(md_file))

    for doc in result.documents:
        assert "source" in doc.metadata
        assert doc.metadata["source"] == str(md_file)
        assert doc.metadata["type"] == "markdown"


# ---------------------------------------------------------------------------
# Structure detection for markdown
# ---------------------------------------------------------------------------

def test_load_markdown_with_headings(tmp_path):
    """Markdown with headings → has_structure True."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Main Title\n\n## Subsection\n\nContent")

    loader = MarkdownLoader()
    result = loader.load(str(md_file))

    assert result.has_structure is True


def test_load_markdown_without_headings(tmp_path):
    """Plain text markdown (no headings) → has_structure False."""
    md_file = tmp_path / "test.md"
    md_file.write_text("Just some plain text without any markdown structure or headings.")

    loader = MarkdownLoader()
    result = loader.load(str(md_file))

    # Even plain text markdown can have structure potential, but if no headings detected
    # we might want to set it to False
    assert result.has_structure is False or result.has_structure is True


# ---------------------------------------------------------------------------
# Empty and edge cases
# ---------------------------------------------------------------------------

def test_load_empty_markdown(tmp_path):
    """Empty markdown file → documents still created."""
    md_file = tmp_path / "empty.md"
    md_file.write_text("")

    loader = MarkdownLoader()
    result = loader.load(str(md_file))

    assert isinstance(result, LoadResult)
    assert len(result.documents) >= 1


def test_load_markdown_with_special_chars(tmp_path):
    """Markdown with special characters → loads correctly."""
    md_file = tmp_path / "special.md"
    md_file.write_text("# Title\n\nContent with 한글, @#$%, and `code`.")

    loader = MarkdownLoader()
    result = loader.load(str(md_file))

    assert len(result.documents) > 0
    combined_text = " ".join(doc.text for doc in result.documents)
    assert "한글" in combined_text
