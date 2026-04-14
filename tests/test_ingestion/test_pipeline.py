from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock, call, patch

import pytest

from backend.ingestion.pipeline import IngestionPipeline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_doc(text: str = "Sample document text") -> MagicMock:
    doc = MagicMock()
    doc.text = text
    return doc


def _make_load_result(
    documents=None,
    fallback_used: bool = False,
    fallback_warning: str | None = None,
    has_structure: bool = True,
) -> MagicMock:
    result = MagicMock()
    result.documents = documents or [_make_doc()]
    result.fallback_used = fallback_used
    result.fallback_warning = fallback_warning
    result.has_structure = has_structure
    return result


def _make_pipeline(on_progress=None, on_warning=None) -> tuple[IngestionPipeline, dict]:
    """Build a pipeline with all dependencies mocked.

    Returns (pipeline, mocks_dict).
    """
    doc_repo = MagicMock()
    index_manager = MagicMock()
    llm = MagicMock()
    embed_model = MagicMock()
    settings_repo = MagicMock()
    settings_repo.get_secret.return_value = "api-key"

    mock_doc = MagicMock()
    mock_doc.id = 1
    mock_doc.title = ""
    doc_repo.create.return_value = mock_doc
    doc_repo.update_status.return_value = mock_doc

    pipeline = IngestionPipeline(
        document_repo=doc_repo,
        index_manager=index_manager,
        llm=llm,
        embed_model=embed_model,
        settings_repo=settings_repo,
        on_progress=on_progress,
        on_warning=on_warning,
    )

    mocks = {
        "doc_repo": doc_repo,
        "index_manager": index_manager,
        "llm": llm,
        "embed_model": embed_model,
        "settings_repo": settings_repo,
        "mock_doc": mock_doc,
    }
    return pipeline, mocks


# ---------------------------------------------------------------------------
# test_ingest_pdf_success
# ---------------------------------------------------------------------------

def test_ingest_pdf_success():
    """Happy path: PDF ingestion succeeds end-to-end."""
    load_result = _make_load_result(
        documents=[_make_doc("## Title\nContent")],
        fallback_used=False,
    )
    mock_node = MagicMock()

    with patch("backend.ingestion.pipeline.PdfLoader") as MockPdfLoader, \
         patch("backend.ingestion.pipeline.Chunker") as MockChunker, \
         patch("backend.ingestion.pipeline.Summarizer") as MockSummarizer, \
         patch("backend.ingestion.pipeline.extract_metadata") as mock_extract:

        MockPdfLoader.return_value.load.return_value = load_result
        MockChunker.return_value.chunk.return_value = [mock_node]
        MockSummarizer.return_value.summarize_document.return_value = "Summary text"
        MockSummarizer.return_value.summarize_chunks.return_value = {}
        mock_extract.return_value = {
            "title": "Test",
            "token_count": 100,
            "source_path": "/test.pdf",
            "source_type": "pdf",
        }

        pipeline, mocks = _make_pipeline()
        result = pipeline.ingest("/test.pdf", "pdf")

    assert result["doc_id"] == 1
    assert result["error"] is None
    assert result["token_count"] == 100

    doc_repo = mocks["doc_repo"]
    status_calls = [c.args[1] for c in doc_repo.update_status.call_args_list]
    assert "processing" in status_calls
    assert "completed" in status_calls


# ---------------------------------------------------------------------------
# test_ingest_with_fallback_sets_warning
# ---------------------------------------------------------------------------

def test_ingest_with_fallback_sets_warning():
    """When loader returns fallback_used=True, set_fallback and on_warning are called."""
    warning_calls = []

    load_result = _make_load_result(
        fallback_used=True,
        fallback_warning="Fallback warning text",
    )
    mock_node = MagicMock()

    with patch("backend.ingestion.pipeline.PdfLoader") as MockPdfLoader, \
         patch("backend.ingestion.pipeline.Chunker") as MockChunker, \
         patch("backend.ingestion.pipeline.Summarizer") as MockSummarizer, \
         patch("backend.ingestion.pipeline.extract_metadata") as mock_extract:

        MockPdfLoader.return_value.load.return_value = load_result
        MockChunker.return_value.chunk.return_value = [mock_node]
        MockSummarizer.return_value.summarize_document.return_value = "Summary"
        MockSummarizer.return_value.summarize_chunks.return_value = {}
        mock_extract.return_value = {
            "title": "Test",
            "token_count": 50,
            "source_path": "/test.pdf",
            "source_type": "pdf",
        }

        pipeline, mocks = _make_pipeline(on_warning=lambda doc_id, msg: warning_calls.append((doc_id, msg)))
        result = pipeline.ingest("/test.pdf", "pdf")

    doc_repo = mocks["doc_repo"]
    doc_repo.set_fallback.assert_called_once_with(1, "Fallback warning text")
    assert len(warning_calls) == 1
    assert warning_calls[0][0] == 1
    assert warning_calls[0][1] == "Fallback warning text"


# ---------------------------------------------------------------------------
# test_ingest_failure_sets_failed_status
# ---------------------------------------------------------------------------

def test_ingest_failure_sets_failed_status():
    """When loader.load raises RuntimeError, status is set to 'failed' and error is returned."""
    with patch("backend.ingestion.pipeline.PdfLoader") as MockPdfLoader, \
         patch("backend.ingestion.pipeline.Chunker"), \
         patch("backend.ingestion.pipeline.Summarizer"):

        MockPdfLoader.return_value.load.side_effect = RuntimeError("Loader exploded")

        pipeline, mocks = _make_pipeline()
        result = pipeline.ingest("/test.pdf", "pdf")

    assert result["error"] is not None
    assert "Loader exploded" in result["error"]
    assert result["token_count"] == 0

    doc_repo = mocks["doc_repo"]
    status_calls = [c.args[1] for c in doc_repo.update_status.call_args_list]
    assert "failed" in status_calls


# ---------------------------------------------------------------------------
# test_ingest_youtube
# ---------------------------------------------------------------------------

def test_ingest_youtube():
    """YouTube ingestion uses YoutubeLoader with openai_api_key."""
    load_result = _make_load_result(
        documents=[_make_doc("Transcript content")],
        has_structure=False,
    )
    mock_node = MagicMock()

    with patch("backend.ingestion.pipeline.YoutubeLoader") as MockYtLoader, \
         patch("backend.ingestion.pipeline.Chunker") as MockChunker, \
         patch("backend.ingestion.pipeline.Summarizer") as MockSummarizer, \
         patch("backend.ingestion.pipeline.extract_metadata") as mock_extract:

        MockYtLoader.return_value.load.return_value = load_result
        MockChunker.return_value.chunk.return_value = [mock_node]
        MockSummarizer.return_value.summarize_document.return_value = "Summary"
        MockSummarizer.return_value.summarize_chunks.return_value = {}
        mock_extract.return_value = {
            "title": "YouTube Video",
            "token_count": 200,
            "source_path": "https://youtube.com/watch?v=abc",
            "source_type": "youtube",
        }

        pipeline, mocks = _make_pipeline()
        result = pipeline.ingest("https://youtube.com/watch?v=abc", "youtube")

    # Verify YoutubeLoader constructed with openai_api_key
    MockYtLoader.assert_called_once_with(openai_api_key="api-key")
    MockYtLoader.return_value.load.assert_called_once_with("https://youtube.com/watch?v=abc")

    assert result["doc_id"] == 1
    assert result["error"] is None


# ---------------------------------------------------------------------------
# test_ingest_markdown
# ---------------------------------------------------------------------------

def test_ingest_markdown():
    """Markdown ingestion uses MarkdownLoader."""
    load_result = _make_load_result(
        documents=[_make_doc("# Title\nMarkdown content")],
        has_structure=True,
    )
    mock_node = MagicMock()

    with patch("backend.ingestion.pipeline.MarkdownLoader") as MockMdLoader, \
         patch("backend.ingestion.pipeline.Chunker") as MockChunker, \
         patch("backend.ingestion.pipeline.Summarizer") as MockSummarizer, \
         patch("backend.ingestion.pipeline.extract_metadata") as mock_extract:

        MockMdLoader.return_value.load.return_value = load_result
        MockChunker.return_value.chunk.return_value = [mock_node]
        MockSummarizer.return_value.summarize_document.return_value = "Summary"
        MockSummarizer.return_value.summarize_chunks.return_value = {}
        mock_extract.return_value = {
            "title": "Title",
            "token_count": 30,
            "source_path": "/doc.md",
            "source_type": "md",
        }

        pipeline, mocks = _make_pipeline()
        result = pipeline.ingest("/doc.md", "md")

    MockMdLoader.assert_called_once_with()
    MockMdLoader.return_value.load.assert_called_once_with("/doc.md")
    assert result["error"] is None


# ---------------------------------------------------------------------------
# test_ingest_text
# ---------------------------------------------------------------------------

def test_ingest_text():
    """Plain text ingestion uses TextLoader."""
    load_result = _make_load_result(
        documents=[_make_doc("Plain text content")],
        has_structure=False,
    )
    mock_node = MagicMock()

    with patch("backend.ingestion.pipeline.TextLoader") as MockTxtLoader, \
         patch("backend.ingestion.pipeline.Chunker") as MockChunker, \
         patch("backend.ingestion.pipeline.Summarizer") as MockSummarizer, \
         patch("backend.ingestion.pipeline.extract_metadata") as mock_extract:

        MockTxtLoader.return_value.load.return_value = load_result
        MockChunker.return_value.chunk.return_value = [mock_node]
        MockSummarizer.return_value.summarize_document.return_value = "Summary"
        MockSummarizer.return_value.summarize_chunks.return_value = {}
        mock_extract.return_value = {
            "title": "Plain Text",
            "token_count": 10,
            "source_path": "/doc.txt",
            "source_type": "txt",
        }

        pipeline, mocks = _make_pipeline()
        result = pipeline.ingest("/doc.txt", "txt")

    MockTxtLoader.assert_called_once_with()
    MockTxtLoader.return_value.load.assert_called_once_with("/doc.txt")
    assert result["error"] is None


# ---------------------------------------------------------------------------
# test_ingest_unknown_type_raises
# ---------------------------------------------------------------------------

def test_ingest_unknown_type_raises():
    """An unknown source_type causes ingest() to return an error (ValueError)."""
    with patch("backend.ingestion.pipeline.Chunker"), \
         patch("backend.ingestion.pipeline.Summarizer"):

        pipeline, mocks = _make_pipeline()
        result = pipeline.ingest("/doc.docx", "docx")

    assert result["error"] is not None
    assert result["doc_id"] == 1

    doc_repo = mocks["doc_repo"]
    status_calls = [c.args[1] for c in doc_repo.update_status.call_args_list]
    assert "failed" in status_calls


# ---------------------------------------------------------------------------
# test_progress_callback_called
# ---------------------------------------------------------------------------

def test_progress_callback_called():
    """on_progress callback is called with correct steps and percentages."""
    progress_calls = []

    def on_progress(doc_id, step, percent):
        progress_calls.append((doc_id, step, percent))

    load_result = _make_load_result()
    mock_node = MagicMock()

    with patch("backend.ingestion.pipeline.PdfLoader") as MockPdfLoader, \
         patch("backend.ingestion.pipeline.Chunker") as MockChunker, \
         patch("backend.ingestion.pipeline.Summarizer") as MockSummarizer, \
         patch("backend.ingestion.pipeline.extract_metadata") as mock_extract:

        MockPdfLoader.return_value.load.return_value = load_result
        MockChunker.return_value.chunk.return_value = [mock_node]
        MockSummarizer.return_value.summarize_document.return_value = "Summary"
        MockSummarizer.return_value.summarize_chunks.return_value = {}
        mock_extract.return_value = {
            "title": "Test",
            "token_count": 100,
            "source_path": "/test.pdf",
            "source_type": "pdf",
        }

        pipeline, mocks = _make_pipeline(on_progress=on_progress)
        pipeline.ingest("/test.pdf", "pdf")

    # Verify specific progress steps are present
    steps = [(step, percent) for (_, step, percent) in progress_calls]
    assert ("extracting", 10) in steps
    assert ("chunking", 30) in steps
    assert ("summarizing", 50) in steps
    assert ("indexing", 70) in steps
    assert ("completed", 100) in steps

    # All calls should use doc_id=1
    for doc_id, _, _ in progress_calls:
        assert doc_id == 1


# ---------------------------------------------------------------------------
# test_ingest_async_returns_doc_id
# ---------------------------------------------------------------------------

def test_ingest_async_returns_doc_id():
    """ingest_async returns an int doc_id immediately without blocking."""
    load_result = _make_load_result()
    mock_node = MagicMock()

    with patch("backend.ingestion.pipeline.PdfLoader") as MockPdfLoader, \
         patch("backend.ingestion.pipeline.Chunker") as MockChunker, \
         patch("backend.ingestion.pipeline.Summarizer") as MockSummarizer, \
         patch("backend.ingestion.pipeline.extract_metadata") as mock_extract:

        MockPdfLoader.return_value.load.return_value = load_result
        MockChunker.return_value.chunk.return_value = [mock_node]
        MockSummarizer.return_value.summarize_document.return_value = "Summary"
        MockSummarizer.return_value.summarize_chunks.return_value = {}
        mock_extract.return_value = {
            "title": "Test",
            "token_count": 100,
            "source_path": "/test.pdf",
            "source_type": "pdf",
        }

        pipeline, mocks = _make_pipeline()
        doc_id = pipeline.ingest_async("/test.pdf", "pdf")

    assert isinstance(doc_id, int)
    assert doc_id == 1
