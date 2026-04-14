from __future__ import annotations

import types
from unittest.mock import MagicMock, patch

import pytest

from backend.ingestion.loaders.pdf_loader import LoadResult, PdfLoader


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_doc(text: str = "Hello world") -> MagicMock:
    """Return a mock document object with a .text attribute."""
    doc = MagicMock()
    doc.text = text
    return doc


# ---------------------------------------------------------------------------
# Tier-1: LlamaParse success
# ---------------------------------------------------------------------------

def test_load_with_llamaparse_success():
    """LlamaParse succeeds → no fallback, no warning."""
    mock_docs = [_make_doc("## Introduction\nSome text")]
    mock_parser_instance = MagicMock()
    mock_parser_instance.load_data.return_value = mock_docs
    mock_llama_parse_cls = MagicMock(return_value=mock_parser_instance)

    with patch.dict("sys.modules", {"llama_cloud": MagicMock(LlamaParse=mock_llama_parse_cls)}):
        # Re-import to pick up patched module inside pdf_loader
        with patch("backend.ingestion.loaders.pdf_loader.LlamaParse", mock_llama_parse_cls):
            loader = PdfLoader(llamaparse_api_key="test-key")
            result = loader.load("dummy.pdf")

    assert isinstance(result, LoadResult)
    assert result.documents == mock_docs
    assert result.fallback_used is False
    assert result.fallback_warning is None
    assert result.has_structure is True  # "##" present


# ---------------------------------------------------------------------------
# Tier-2: LlamaParse fails → OpenDataLoader
# ---------------------------------------------------------------------------

def test_load_falls_back_to_opendataloader():
    """LlamaParse raises → OpenDataLoader returns documents."""
    mock_docs = [_make_doc("Plain text without headings")]

    mock_llama_parse_cls = MagicMock(side_effect=Exception("LlamaParse unavailable"))

    mock_odl_loader_instance = MagicMock()
    mock_odl_loader_instance.load_data.return_value = mock_docs
    mock_odl_loader_cls = MagicMock(return_value=mock_odl_loader_instance)
    mock_odl_module = types.SimpleNamespace(OpenDataLoader=mock_odl_loader_cls)

    with patch("backend.ingestion.loaders.pdf_loader.LlamaParse", mock_llama_parse_cls), \
         patch("backend.ingestion.loaders.pdf_loader._try_opendataloader", wraps=None) as mock_try_odl:
        # Bypass _try_opendataloader wrapper and test through the real code path
        # by patching the internal import inside _try_opendataloader
        pass

    # Use a more direct approach: patch the function itself
    mock_odl_docs = [_make_doc("Content from OpenDataLoader")]

    def fake_try_opendataloader(file_path: str):
        return mock_odl_docs

    with patch("backend.ingestion.loaders.pdf_loader.LlamaParse", mock_llama_parse_cls), \
         patch("backend.ingestion.loaders.pdf_loader._try_opendataloader", side_effect=fake_try_opendataloader):
        loader = PdfLoader(llamaparse_api_key="test-key")
        result = loader.load("dummy.pdf")

    assert result.fallback_used is True
    assert result.fallback_warning is not None
    assert "OpenDataLoader" in result.fallback_warning
    assert result.documents == mock_odl_docs


# ---------------------------------------------------------------------------
# Tier-3: LlamaParse fails + OpenDataLoader fails → LiteParse
# ---------------------------------------------------------------------------

def test_load_falls_back_to_liteparse():
    """LlamaParse and OpenDataLoader both fail → LiteParse returns documents."""
    mock_docs = [_make_doc("Basic text")]

    mock_llama_parse_cls = MagicMock(side_effect=Exception("LlamaParse unavailable"))

    def fail_opendataloader(file_path: str):
        raise Exception("OpenDataLoader unavailable")

    mock_lite_parser_instance = MagicMock()
    mock_lite_parser_instance.load_data.return_value = mock_docs
    mock_lite_parser_cls = MagicMock(return_value=mock_lite_parser_instance)

    with patch("backend.ingestion.loaders.pdf_loader.LlamaParse", mock_llama_parse_cls), \
         patch("backend.ingestion.loaders.pdf_loader._try_opendataloader", side_effect=fail_opendataloader), \
         patch("backend.ingestion.loaders.pdf_loader.LiteParser", mock_lite_parser_cls):
        loader = PdfLoader(llamaparse_api_key="test-key")
        result = loader.load("dummy.pdf")

    assert result.fallback_used is True
    assert result.fallback_warning is not None
    assert "기본 파서" in result.fallback_warning
    assert result.documents == mock_docs


# ---------------------------------------------------------------------------
# All fail → RuntimeError
# ---------------------------------------------------------------------------

def test_load_all_fail_raises():
    """All three tiers fail → RuntimeError is raised."""
    mock_llama_parse_cls = MagicMock(side_effect=Exception("LlamaParse unavailable"))

    def fail_opendataloader(file_path: str):
        raise Exception("OpenDataLoader unavailable")

    mock_lite_parser_cls = MagicMock(side_effect=Exception("LiteParse unavailable"))

    with patch("backend.ingestion.loaders.pdf_loader.LlamaParse", mock_llama_parse_cls), \
         patch("backend.ingestion.loaders.pdf_loader._try_opendataloader", side_effect=fail_opendataloader), \
         patch("backend.ingestion.loaders.pdf_loader.LiteParser", mock_lite_parser_cls):
        loader = PdfLoader(llamaparse_api_key="test-key")
        with pytest.raises(RuntimeError):
            loader.load("dummy.pdf")


# ---------------------------------------------------------------------------
# Structure detection
# ---------------------------------------------------------------------------

def test_detect_structure_with_headings():
    """Document containing '# Title' → has_structure True."""
    mock_docs = [_make_doc("# Title\nSome content")]
    mock_parser_instance = MagicMock()
    mock_parser_instance.load_data.return_value = mock_docs
    mock_llama_parse_cls = MagicMock(return_value=mock_parser_instance)

    with patch("backend.ingestion.loaders.pdf_loader.LlamaParse", mock_llama_parse_cls):
        loader = PdfLoader(llamaparse_api_key="test-key")
        result = loader.load("dummy.pdf")

    assert result.has_structure is True


def test_detect_structure_without_headings():
    """Document with no heading markers → has_structure False."""
    mock_docs = [_make_doc("Plain paragraph without any headings at all.")]
    mock_parser_instance = MagicMock()
    mock_parser_instance.load_data.return_value = mock_docs
    mock_llama_parse_cls = MagicMock(return_value=mock_parser_instance)

    with patch("backend.ingestion.loaders.pdf_loader.LlamaParse", mock_llama_parse_cls):
        loader = PdfLoader(llamaparse_api_key="test-key")
        result = loader.load("dummy.pdf")

    assert result.has_structure is False


def test_detect_structure_with_h2_headings():
    """Document containing '## Section' → has_structure True."""
    mock_docs = [_make_doc("## Section\nMore content")]
    mock_parser_instance = MagicMock()
    mock_parser_instance.load_data.return_value = mock_docs
    mock_llama_parse_cls = MagicMock(return_value=mock_parser_instance)

    with patch("backend.ingestion.loaders.pdf_loader.LlamaParse", mock_llama_parse_cls):
        loader = PdfLoader(llamaparse_api_key="test-key")
        result = loader.load("dummy.pdf")

    assert result.has_structure is True
