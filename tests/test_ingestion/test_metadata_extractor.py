from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# test_count_tokens
# ---------------------------------------------------------------------------

def test_count_tokens_returns_positive_int():
    """'hello world' should return a small positive integer."""
    from backend.ingestion.metadata_extractor import count_tokens
    result = count_tokens("hello world")
    assert isinstance(result, int)
    assert result > 0


def test_count_tokens_longer_text():
    from backend.ingestion.metadata_extractor import count_tokens
    short = count_tokens("hi")
    long = count_tokens("hi " * 100)
    assert long > short


def test_count_tokens_empty_string():
    from backend.ingestion.metadata_extractor import count_tokens
    result = count_tokens("")
    assert result == 0


def test_count_tokens_default_model():
    """count_tokens should work with no model argument (defaults to gpt-4o)."""
    from backend.ingestion.metadata_extractor import count_tokens
    result = count_tokens("test token counting")
    assert result > 0


def test_count_tokens_fallback_when_model_unknown():
    """Unknown model should fall back to cl100k_base encoding."""
    from backend.ingestion.metadata_extractor import count_tokens
    result = count_tokens("test text", model="unknown-model-xyz")
    assert isinstance(result, int)
    assert result > 0


# ---------------------------------------------------------------------------
# test_extract_title_from_heading
# ---------------------------------------------------------------------------

def test_extract_title_from_heading():
    mock_doc = MagicMock(text="# My Document Title\n\nContent here")
    from backend.ingestion.metadata_extractor import extract_metadata
    meta = extract_metadata([mock_doc], "/path/doc.pdf", "pdf")
    assert meta["title"] == "My Document Title"


def test_extract_title_from_h2_heading():
    """## heading should also be recognized as a title."""
    mock_doc = MagicMock(text="## Section Title\n\nBody text here")
    from backend.ingestion.metadata_extractor import extract_metadata
    meta = extract_metadata([mock_doc], "/path/some_doc.pdf", "pdf")
    assert meta["title"] == "Section Title"


# ---------------------------------------------------------------------------
# test_extract_title_fallback_to_filename
# ---------------------------------------------------------------------------

def test_extract_title_fallback_to_filename():
    mock_doc = MagicMock(text="No heading here, just plain text")
    from backend.ingestion.metadata_extractor import extract_metadata
    meta = extract_metadata([mock_doc], "/path/my-cool-document.pdf", "pdf")
    assert "My Cool Document" in meta["title"]


def test_extract_title_fallback_underscored_filename():
    mock_doc = MagicMock(text="Plain content with no heading.")
    from backend.ingestion.metadata_extractor import extract_metadata
    meta = extract_metadata([mock_doc], "/docs/machine_learning_guide.txt", "txt")
    assert "Machine Learning Guide" in meta["title"]


# ---------------------------------------------------------------------------
# test_extract_metadata structure
# ---------------------------------------------------------------------------

def test_extract_metadata_contains_required_keys():
    mock_doc = MagicMock(text="# Title\n\nSome content here.")
    from backend.ingestion.metadata_extractor import extract_metadata
    meta = extract_metadata([mock_doc], "/path/file.pdf", "pdf")
    assert "title" in meta
    assert "source_path" in meta
    assert "source_type" in meta
    assert "token_count" in meta


def test_extract_metadata_source_path():
    mock_doc = MagicMock(text="# My Doc\n\nContent.")
    from backend.ingestion.metadata_extractor import extract_metadata
    meta = extract_metadata([mock_doc], "/some/path/file.pdf", "pdf")
    assert meta["source_path"] == "/some/path/file.pdf"


def test_extract_metadata_source_type():
    mock_doc = MagicMock(text="Content without heading.")
    from backend.ingestion.metadata_extractor import extract_metadata
    meta = extract_metadata([mock_doc], "/path/file.md", "markdown")
    assert meta["source_type"] == "markdown"


def test_extract_metadata_token_count_positive():
    mock_doc = MagicMock(text="This document has multiple tokens in it for counting purposes.")
    from backend.ingestion.metadata_extractor import extract_metadata
    meta = extract_metadata([mock_doc], "/path/file.pdf", "pdf")
    assert isinstance(meta["token_count"], int)
    assert meta["token_count"] > 0


def test_extract_metadata_multiple_docs():
    """Multiple documents should concatenate text for token counting."""
    doc1 = MagicMock(text="# Title Doc\n\nFirst document content.")
    doc2 = MagicMock(text="Second document content that extends the first.")
    from backend.ingestion.metadata_extractor import extract_metadata
    meta_single = extract_metadata([doc1], "/path/file.pdf", "pdf")
    meta_combined = extract_metadata([doc1, doc2], "/path/file.pdf", "pdf")
    assert meta_combined["token_count"] > meta_single["token_count"]


def test_extract_title_prefers_first_doc_heading():
    """Title extracted from first document's first heading."""
    doc1 = MagicMock(text="# First Doc Title\n\nContent.")
    doc2 = MagicMock(text="# Second Doc Title\n\nOther content.")
    from backend.ingestion.metadata_extractor import extract_metadata
    meta = extract_metadata([doc1, doc2], "/path/file.pdf", "pdf")
    assert meta["title"] == "First Doc Title"
