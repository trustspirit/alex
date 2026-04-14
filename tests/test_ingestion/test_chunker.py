from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from backend.ingestion.chunker import Chunker


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_doc(text: str = "Sample document text.") -> MagicMock:
    """Return a mock document object with a .text attribute."""
    doc = MagicMock()
    doc.text = text
    return doc


def _make_node(text: str = "Sample node text.") -> MagicMock:
    """Return a mock node object."""
    node = MagicMock()
    node.text = text
    return node


# ---------------------------------------------------------------------------
# test_empty_documents_returns_empty
# ---------------------------------------------------------------------------

def test_empty_documents_returns_empty():
    """documents=[] → returns [] immediately without calling any parser."""
    chunker = Chunker()
    result = chunker.chunk(documents=[], has_structure=True)
    assert result == []


def test_empty_documents_returns_empty_unstructured():
    """documents=[] with has_structure=False → returns [] as well."""
    chunker = Chunker()
    result = chunker.chunk(documents=[], has_structure=False)
    assert result == []


# ---------------------------------------------------------------------------
# test_structured_document_uses_hierarchical
# ---------------------------------------------------------------------------

def test_structured_document_uses_hierarchical():
    """has_structure=True → HierarchicalNodeParser is used; returns nodes."""
    docs = [_make_doc("# Heading\nSome content under heading.")]
    mock_nodes = [_make_node("Node 1"), _make_node("Node 2")]

    mock_parser_instance = MagicMock()
    mock_parser_instance.get_nodes_from_documents.return_value = mock_nodes
    mock_parser_cls = MagicMock(return_value=mock_parser_instance)

    with patch("backend.ingestion.chunker.HierarchicalNodeParser", mock_parser_cls):
        chunker = Chunker(chunk_sizes=[1024, 512, 256])
        result = chunker.chunk(documents=docs, has_structure=True)

    mock_parser_cls.assert_called_once()
    mock_parser_instance.get_nodes_from_documents.assert_called_once_with(docs)
    assert result == mock_nodes


def test_structured_document_passes_chunk_sizes():
    """HierarchicalNodeParser is constructed with the configured chunk_sizes."""
    docs = [_make_doc("## Section\nText")]
    mock_nodes = [_make_node()]

    mock_parser_instance = MagicMock()
    mock_parser_instance.get_nodes_from_documents.return_value = mock_nodes
    mock_parser_cls = MagicMock(return_value=mock_parser_instance)

    custom_sizes = [2048, 1024, 512]
    with patch("backend.ingestion.chunker.HierarchicalNodeParser", mock_parser_cls):
        chunker = Chunker(chunk_sizes=custom_sizes)
        chunker.chunk(documents=docs, has_structure=True)

    # Verify chunk_sizes were passed to the constructor
    call_kwargs = mock_parser_cls.call_args
    assert call_kwargs is not None
    # chunk_sizes may be passed as positional or keyword argument
    args, kwargs = call_kwargs
    assert kwargs.get("chunk_sizes") == custom_sizes or (
        len(args) > 0 and custom_sizes in args
    )


# ---------------------------------------------------------------------------
# test_unstructured_document_with_embed_model_uses_semantic
# ---------------------------------------------------------------------------

def test_unstructured_document_with_embed_model_uses_semantic():
    """has_structure=False with embed_model → SemanticSplitterNodeParser is used."""
    docs = [_make_doc("Plain unstructured text without any headings at all.")]
    mock_embed_model = MagicMock()
    mock_nodes = [_make_node("Semantic node")]

    mock_parser_instance = MagicMock()
    mock_parser_instance.get_nodes_from_documents.return_value = mock_nodes
    mock_semantic_cls = MagicMock(return_value=mock_parser_instance)

    with patch("backend.ingestion.chunker.SemanticSplitterNodeParser", mock_semantic_cls):
        chunker = Chunker()
        result = chunker.chunk(
            documents=docs, has_structure=False, embed_model=mock_embed_model
        )

    mock_semantic_cls.assert_called_once()
    mock_parser_instance.get_nodes_from_documents.assert_called_once_with(docs)
    assert result == mock_nodes


def test_unstructured_with_embed_model_passes_embed_model():
    """SemanticSplitterNodeParser is constructed with the embed_model."""
    docs = [_make_doc("Some unstructured text.")]
    mock_embed_model = MagicMock()
    mock_nodes = [_make_node()]

    mock_parser_instance = MagicMock()
    mock_parser_instance.get_nodes_from_documents.return_value = mock_nodes
    mock_semantic_cls = MagicMock(return_value=mock_parser_instance)

    with patch("backend.ingestion.chunker.SemanticSplitterNodeParser", mock_semantic_cls):
        chunker = Chunker()
        chunker.chunk(documents=docs, has_structure=False, embed_model=mock_embed_model)

    call_kwargs = mock_semantic_cls.call_args
    assert call_kwargs is not None
    args, kwargs = call_kwargs
    assert kwargs.get("embed_model") == mock_embed_model or mock_embed_model in args


# ---------------------------------------------------------------------------
# test_unstructured_document_without_embed_model_uses_sentence
# ---------------------------------------------------------------------------

def test_unstructured_document_without_embed_model_uses_sentence():
    """has_structure=False, embed_model=None → SentenceSplitter fallback."""
    docs = [_make_doc("Plain text without any embed model provided.")]
    mock_nodes = [_make_node("Sentence node")]

    mock_parser_instance = MagicMock()
    mock_parser_instance.get_nodes_from_documents.return_value = mock_nodes
    mock_sentence_cls = MagicMock(return_value=mock_parser_instance)

    with patch("backend.ingestion.chunker.SentenceSplitter", mock_sentence_cls):
        chunker = Chunker()
        result = chunker.chunk(documents=docs, has_structure=False, embed_model=None)

    mock_sentence_cls.assert_called_once()
    mock_parser_instance.get_nodes_from_documents.assert_called_once_with(docs)
    assert result == mock_nodes


def test_unstructured_without_embed_uses_default_chunk_size():
    """SentenceSplitter is constructed with chunk_size=512 and chunk_overlap=50."""
    docs = [_make_doc("Some text.")]
    mock_nodes = [_make_node()]

    mock_parser_instance = MagicMock()
    mock_parser_instance.get_nodes_from_documents.return_value = mock_nodes
    mock_sentence_cls = MagicMock(return_value=mock_parser_instance)

    with patch("backend.ingestion.chunker.SentenceSplitter", mock_sentence_cls):
        chunker = Chunker()
        chunker.chunk(documents=docs, has_structure=False, embed_model=None)

    call_kwargs = mock_sentence_cls.call_args
    assert call_kwargs is not None
    args, kwargs = call_kwargs
    assert kwargs.get("chunk_size") == 512
    assert kwargs.get("chunk_overlap") == 50


# ---------------------------------------------------------------------------
# test_semantic_failure_falls_back_to_sentence
# ---------------------------------------------------------------------------

def test_semantic_failure_falls_back_to_sentence():
    """SemanticSplitter raises an exception → falls back to SentenceSplitter."""
    docs = [_make_doc("Unstructured text that triggers semantic failure.")]
    mock_embed_model = MagicMock()
    mock_nodes = [_make_node("Fallback sentence node")]

    mock_semantic_instance = MagicMock()
    mock_semantic_instance.get_nodes_from_documents.side_effect = Exception(
        "SemanticSplitter failed"
    )
    mock_semantic_cls = MagicMock(return_value=mock_semantic_instance)

    mock_sentence_instance = MagicMock()
    mock_sentence_instance.get_nodes_from_documents.return_value = mock_nodes
    mock_sentence_cls = MagicMock(return_value=mock_sentence_instance)

    with patch("backend.ingestion.chunker.SemanticSplitterNodeParser", mock_semantic_cls), \
         patch("backend.ingestion.chunker.SentenceSplitter", mock_sentence_cls):
        chunker = Chunker()
        result = chunker.chunk(
            documents=docs, has_structure=False, embed_model=mock_embed_model
        )

    # Semantic was attempted but failed
    mock_semantic_instance.get_nodes_from_documents.assert_called_once_with(docs)
    # Sentence splitter was used as fallback
    mock_sentence_cls.assert_called_once()
    mock_sentence_instance.get_nodes_from_documents.assert_called_once_with(docs)
    assert result == mock_nodes


def test_semantic_init_failure_falls_back_to_sentence():
    """SemanticSplitter constructor raises → falls back to SentenceSplitter."""
    docs = [_make_doc("Some text.")]
    mock_embed_model = MagicMock()
    mock_nodes = [_make_node("Fallback node")]

    mock_semantic_cls = MagicMock(side_effect=Exception("SemanticSplitter not available"))

    mock_sentence_instance = MagicMock()
    mock_sentence_instance.get_nodes_from_documents.return_value = mock_nodes
    mock_sentence_cls = MagicMock(return_value=mock_sentence_instance)

    with patch("backend.ingestion.chunker.SemanticSplitterNodeParser", mock_semantic_cls), \
         patch("backend.ingestion.chunker.SentenceSplitter", mock_sentence_cls):
        chunker = Chunker()
        result = chunker.chunk(
            documents=docs, has_structure=False, embed_model=mock_embed_model
        )

    mock_sentence_cls.assert_called_once()
    assert result == mock_nodes


# ---------------------------------------------------------------------------
# Default chunk_sizes
# ---------------------------------------------------------------------------

def test_default_chunk_sizes():
    """Chunker uses [1024, 512, 256] when no chunk_sizes argument is given."""
    chunker = Chunker()
    assert chunker._chunk_sizes == [1024, 512, 256]


def test_custom_chunk_sizes():
    """Chunker stores custom chunk_sizes when provided."""
    chunker = Chunker(chunk_sizes=[2048, 1024])
    assert chunker._chunk_sizes == [2048, 1024]
