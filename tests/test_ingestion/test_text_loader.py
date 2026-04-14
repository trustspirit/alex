from __future__ import annotations

from pathlib import Path

import pytest

from backend.ingestion.loaders.text_loader import LoadResult, TextLoader


# ---------------------------------------------------------------------------
# Basic text loading test
# ---------------------------------------------------------------------------

def test_load_text(tmp_path):
    """Load a simple text file and verify basic loading works."""
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("Line 1\nLine 2\nLine 3")

    loader = TextLoader()
    result = loader.load(str(txt_file))

    assert isinstance(result, LoadResult)
    assert len(result.documents) == 1
    assert "Line 1" in result.documents[0].text
    assert result.has_structure is False
    assert result.fallback_used is False
    assert result.fallback_warning is None


# ---------------------------------------------------------------------------
# Verify document content and metadata
# ---------------------------------------------------------------------------

def test_load_text_contains_full_content(tmp_path):
    """Text file should be loaded as a single document with full content."""
    txt_file = tmp_path / "test.txt"
    content = "This is line 1\nThis is line 2\nThis is line 3"
    txt_file.write_text(content)

    loader = TextLoader()
    result = loader.load(str(txt_file))

    assert len(result.documents) == 1
    assert result.documents[0].text == content


def test_load_text_metadata(tmp_path):
    """Text documents should have correct metadata."""
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("Some text content")

    loader = TextLoader()
    result = loader.load(str(txt_file))

    doc = result.documents[0]
    assert "source" in doc.metadata
    assert doc.metadata["source"] == str(txt_file)
    assert doc.metadata["type"] == "text"


# ---------------------------------------------------------------------------
# Structure detection for plain text
# ---------------------------------------------------------------------------

def test_load_text_has_no_structure(tmp_path):
    """Plain text is always unstructured."""
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("# This is just text\n\n## Not markdown")

    loader = TextLoader()
    result = loader.load(str(txt_file))

    # Even if the text contains markdown-like chars, plain text has no structure
    assert result.has_structure is False


# ---------------------------------------------------------------------------
# Empty and edge cases
# ---------------------------------------------------------------------------

def test_load_empty_text(tmp_path):
    """Empty text file → single document with empty text."""
    txt_file = tmp_path / "empty.txt"
    txt_file.write_text("")

    loader = TextLoader()
    result = loader.load(str(txt_file))

    assert len(result.documents) == 1
    assert result.documents[0].text == ""


def test_load_text_with_special_chars(tmp_path):
    """Text file with special characters → loads correctly."""
    txt_file = tmp_path / "special.txt"
    content = "Special chars: 한글, @#$%, `code`, and\ttabs\nMultiple\n\nNewlines"
    txt_file.write_text(content)

    loader = TextLoader()
    result = loader.load(str(txt_file))

    assert len(result.documents) == 1
    assert result.documents[0].text == content
    assert "한글" in result.documents[0].text


def test_load_text_with_long_content(tmp_path):
    """Text file with long content → loads as single document."""
    txt_file = tmp_path / "long.txt"
    lines = [f"Line {i}" for i in range(1000)]
    content = "\n".join(lines)
    txt_file.write_text(content)

    loader = TextLoader()
    result = loader.load(str(txt_file))

    assert len(result.documents) == 1
    assert "Line 0" in result.documents[0].text
    assert "Line 999" in result.documents[0].text
