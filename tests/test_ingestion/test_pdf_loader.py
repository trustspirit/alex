from __future__ import annotations

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


def _mock_llamacloud(pages_data):
    """Create a mock _LlamaCloud class that returns pages_data from parsing.parse()."""
    mock_pages = []
    for p in pages_data:
        page = MagicMock()
        page.markdown = p["text"]
        page.page_number = p.get("page", 1)
        mock_pages.append(page)

    mock_markdown = MagicMock()
    mock_markdown.pages = mock_pages

    mock_result = MagicMock()
    mock_result.markdown = mock_markdown

    mock_parsing = MagicMock()
    mock_parsing.parse.return_value = mock_result

    mock_client = MagicMock()
    mock_client.parsing = mock_parsing

    mock_cls = MagicMock(return_value=mock_client)
    return mock_cls


def _mock_llamacloud_fail(error_msg="API error"):
    """Create a mock _LlamaCloud class that raises on parse()."""
    mock_parsing = MagicMock()
    mock_parsing.parse.side_effect = Exception(error_msg)

    mock_client = MagicMock()
    mock_client.parsing = mock_parsing

    mock_cls = MagicMock(return_value=mock_client)
    return mock_cls


# ---------------------------------------------------------------------------
# Tier-1: LlamaParse success
# ---------------------------------------------------------------------------

def test_load_with_llamaparse_success():
    """LlamaParse succeeds → no fallback, no warning."""
    mock_cls = _mock_llamacloud([
        {"text": "## Introduction\nSome text", "page": 1},
    ])

    with patch("backend.ingestion.loaders.pdf_loader._LlamaCloud", mock_cls), \
         patch("builtins.open", MagicMock()):
        loader = PdfLoader(llamaparse_api_key="test-key")
        result = loader.load("dummy.pdf")

    assert isinstance(result, LoadResult)
    assert len(result.documents) == 1
    assert result.fallback_used is False
    assert result.fallback_warning is None
    assert result.has_structure is True  # "##" present


# ---------------------------------------------------------------------------
# Tier-2: LlamaParse fails → OpenDataLoader
# ---------------------------------------------------------------------------

def test_load_falls_back_to_opendataloader():
    """LlamaParse raises → OpenDataLoader returns documents."""
    mock_llama = _mock_llamacloud_fail()
    mock_odl_docs = [_make_doc("Content from OpenDataLoader")]

    def fake_try_opendataloader(file_path: str):
        return mock_odl_docs

    with patch("backend.ingestion.loaders.pdf_loader._LlamaCloud", mock_llama), \
         patch("backend.ingestion.loaders.pdf_loader._try_opendataloader", side_effect=fake_try_opendataloader):
        loader = PdfLoader(llamaparse_api_key="test-key")
        result = loader.load("dummy.pdf")

    assert result.fallback_used is True
    assert "OpenDataLoader" in result.fallback_warning
    assert result.documents == mock_odl_docs


# ---------------------------------------------------------------------------
# Tier-3: LlamaParse fails + OpenDataLoader fails → LiteParse
# ---------------------------------------------------------------------------

def test_load_falls_back_to_liteparse():
    """LlamaParse and OpenDataLoader both fail → LiteParse returns documents."""
    mock_llama = _mock_llamacloud_fail()

    def fail_opendataloader(file_path: str):
        raise Exception("OpenDataLoader unavailable")

    mock_page = MagicMock()
    mock_page.text = "Fallback parsed content"
    mock_parse_result = MagicMock()
    mock_parse_result.num_pages = 1
    mock_parse_result.get_page.return_value = mock_page

    mock_liteparse_instance = MagicMock()
    mock_liteparse_instance.parse.return_value = mock_parse_result
    mock_liteparse_cls = MagicMock(return_value=mock_liteparse_instance)

    with patch("backend.ingestion.loaders.pdf_loader._LlamaCloud", mock_llama), \
         patch("backend.ingestion.loaders.pdf_loader._try_opendataloader", side_effect=fail_opendataloader), \
         patch("backend.ingestion.loaders.pdf_loader._LiteParse", mock_liteparse_cls):
        loader = PdfLoader(llamaparse_api_key="test-key")
        result = loader.load("dummy.pdf")

    assert result.fallback_used is True
    assert "기본 파서" in result.fallback_warning
    assert len(result.documents) == 1


# ---------------------------------------------------------------------------
# All fail → RuntimeError
# ---------------------------------------------------------------------------

def test_load_all_fail_raises():
    """All three tiers fail → RuntimeError is raised."""
    mock_llama = _mock_llamacloud_fail()

    def fail_opendataloader(file_path: str):
        raise Exception("OpenDataLoader unavailable")

    mock_liteparse_cls = MagicMock(side_effect=Exception("LiteParse unavailable"))

    with patch("backend.ingestion.loaders.pdf_loader._LlamaCloud", mock_llama), \
         patch("backend.ingestion.loaders.pdf_loader._try_opendataloader", side_effect=fail_opendataloader), \
         patch("backend.ingestion.loaders.pdf_loader._LiteParse", mock_liteparse_cls):
        loader = PdfLoader(llamaparse_api_key="test-key")
        with pytest.raises(RuntimeError):
            loader.load("dummy.pdf")


# ---------------------------------------------------------------------------
# No API key → skip LlamaParse immediately
# ---------------------------------------------------------------------------

def test_no_api_key_skips_llamaparse():
    """No API key → LlamaParse is skipped, falls through to next tier."""
    mock_page = MagicMock()
    mock_page.text = "LiteParse content"
    mock_parse_result = MagicMock()
    mock_parse_result.num_pages = 1
    mock_parse_result.get_page.return_value = mock_page

    mock_liteparse_instance = MagicMock()
    mock_liteparse_instance.parse.return_value = mock_parse_result
    mock_liteparse_cls = MagicMock(return_value=mock_liteparse_instance)

    def fail_opendataloader(file_path: str):
        raise Exception("No Java")

    with patch("backend.ingestion.loaders.pdf_loader._try_opendataloader", side_effect=fail_opendataloader), \
         patch("backend.ingestion.loaders.pdf_loader._LiteParse", mock_liteparse_cls):
        loader = PdfLoader(llamaparse_api_key="")  # No key
        result = loader.load("dummy.pdf")

    assert result.fallback_used is True
    assert len(result.documents) == 1


# ---------------------------------------------------------------------------
# Structure detection
# ---------------------------------------------------------------------------

def test_detect_structure_with_headings():
    """Document containing '# Title' → has_structure True."""
    mock_cls = _mock_llamacloud([{"text": "# Title\nSome content"}])

    with patch("backend.ingestion.loaders.pdf_loader._LlamaCloud", mock_cls), \
         patch("builtins.open", MagicMock()):
        loader = PdfLoader(llamaparse_api_key="test-key")
        result = loader.load("dummy.pdf")

    assert result.has_structure is True


def test_detect_structure_without_headings():
    """Document with no heading markers → has_structure False."""
    mock_cls = _mock_llamacloud([{"text": "Plain paragraph without headings."}])

    with patch("backend.ingestion.loaders.pdf_loader._LlamaCloud", mock_cls), \
         patch("builtins.open", MagicMock()):
        loader = PdfLoader(llamaparse_api_key="test-key")
        result = loader.load("dummy.pdf")

    assert result.has_structure is False
