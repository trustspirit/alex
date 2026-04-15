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
# Tier-2: LlamaParse fails → MinerU
# ---------------------------------------------------------------------------

def test_load_falls_back_to_mineru():
    mock_llama = _mock_llamacloud_fail()
    with patch("backend.ingestion.loaders.pdf_loader._LlamaCloud", mock_llama), \
         patch("backend.ingestion.loaders.pdf_loader.PdfLoader._load_mineru") as mock_mineru:
        mock_mineru.return_value = [_make_doc("Page 1"), _make_doc("Page 2")]
        loader = PdfLoader(llamaparse_api_key="test-key")
        result = loader.load("dummy.pdf")
    assert result.fallback_used is True
    assert "MinerU" in result.fallback_warning
    assert len(result.documents) == 2


# ---------------------------------------------------------------------------
# Tier-2 fails → Tier-3: MinerU fails → OpenDataLoader
# ---------------------------------------------------------------------------

def test_mineru_fallback_to_opendataloader():
    mock_llama = _mock_llamacloud_fail()
    mock_odl_docs = [_make_doc("ODL content")]
    with patch("backend.ingestion.loaders.pdf_loader._LlamaCloud", mock_llama), \
         patch("backend.ingestion.loaders.pdf_loader.PdfLoader._load_mineru", side_effect=Exception("MinerU failed")), \
         patch("backend.ingestion.loaders.pdf_loader._try_opendataloader", return_value=mock_odl_docs):
        loader = PdfLoader(llamaparse_api_key="test-key")
        result = loader.load("dummy.pdf")
    assert result.fallback_used is True
    assert "OpenDataLoader" in result.fallback_warning


def test_load_falls_back_to_opendataloader():
    """LlamaParse and MinerU both fail → OpenDataLoader returns documents."""
    mock_llama = _mock_llamacloud_fail()
    mock_odl_docs = [_make_doc("Content from OpenDataLoader")]

    def fake_try_opendataloader(file_path: str):
        return mock_odl_docs

    with patch("backend.ingestion.loaders.pdf_loader._LlamaCloud", mock_llama), \
         patch("backend.ingestion.loaders.pdf_loader.PdfLoader._load_mineru", side_effect=Exception("MinerU failed")), \
         patch("backend.ingestion.loaders.pdf_loader._try_opendataloader", side_effect=fake_try_opendataloader):
        loader = PdfLoader(llamaparse_api_key="test-key")
        result = loader.load("dummy.pdf")

    assert result.fallback_used is True
    assert "OpenDataLoader" in result.fallback_warning
    assert result.documents == mock_odl_docs


# ---------------------------------------------------------------------------
# All fail → RuntimeError
# ---------------------------------------------------------------------------

def test_load_all_fail_raises():
    """All three tiers fail → RuntimeError is raised."""
    mock_llama = _mock_llamacloud_fail()
    with patch("backend.ingestion.loaders.pdf_loader._LlamaCloud", mock_llama), \
         patch("backend.ingestion.loaders.pdf_loader.PdfLoader._load_mineru", side_effect=Exception("MinerU failed")), \
         patch("backend.ingestion.loaders.pdf_loader._try_opendataloader", side_effect=Exception("ODL failed")):
        loader = PdfLoader(llamaparse_api_key="test-key")
        with pytest.raises(RuntimeError):
            loader.load("dummy.pdf")


# ---------------------------------------------------------------------------
# No API key → skip LlamaParse immediately
# ---------------------------------------------------------------------------

def test_no_api_key_skips_llamaparse_uses_mineru():
    """No API key → LlamaParse is skipped, falls through to MinerU."""
    with patch("backend.ingestion.loaders.pdf_loader.PdfLoader._load_mineru") as mock_mineru:
        mock_mineru.return_value = [_make_doc("## Heading\nMinerU content")]
        loader = PdfLoader(llamaparse_api_key="")
        result = loader.load("dummy.pdf")
    assert result.fallback_used is True
    assert "MinerU" in result.fallback_warning
    assert result.has_structure is True


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


# ---------------------------------------------------------------------------
# _build_page_documents unit tests
# ---------------------------------------------------------------------------

def test_build_page_documents_with_page_idx():
    """content_list with page_idx → page-level Documents."""
    loader = PdfLoader()
    content_list = [
        {"page_idx": 0, "text": "First page content"},
        {"page_idx": 0, "text": "More first page"},
        {"page_idx": 1, "text": "Second page content"},
    ]
    docs = loader._build_page_documents(content_list, None, "test.pdf")
    assert len(docs) == 2
    assert "First page content" in docs[0].text
    assert "More first page" in docs[0].text
    assert docs[0].metadata["page_label"] == "1"
    assert docs[1].metadata["page_label"] == "2"
    assert docs[1].metadata["method"] == "mineru"


def test_build_page_documents_markdown_fallback():
    """No content_list → falls back to whole markdown."""
    loader = PdfLoader()
    docs = loader._build_page_documents(None, "# Title\nSome content", "test.pdf")
    assert len(docs) == 1
    assert "Title" in docs[0].text
    assert docs[0].metadata["method"] == "mineru"


def test_build_page_documents_empty():
    """No content_list and no markdown → empty list."""
    loader = PdfLoader()
    docs = loader._build_page_documents(None, None, "test.pdf")
    assert docs == []


def test_build_page_documents_empty_content_list():
    """Empty content_list → falls back to markdown."""
    loader = PdfLoader()
    docs = loader._build_page_documents([], "Fallback markdown", "test.pdf")
    assert len(docs) == 1
    assert "Fallback markdown" in docs[0].text


def test_build_page_documents_skips_blank_text():
    """Items with blank text are skipped."""
    loader = PdfLoader()
    content_list = [
        {"page_idx": 0, "text": "Real content"},
        {"page_idx": 0, "text": "   "},
        {"page_idx": 1, "text": ""},
    ]
    docs = loader._build_page_documents(content_list, None, "test.pdf")
    assert len(docs) == 1
    assert docs[0].metadata["page_label"] == "1"
