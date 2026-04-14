from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from backend.ingestion.summarizer import Summarizer


# ---------------------------------------------------------------------------
# test_generate_document_summary
# ---------------------------------------------------------------------------

def test_generate_document_summary():
    mock_llm = MagicMock()
    mock_llm.complete.return_value = MagicMock(text="This document discusses...")
    summarizer = Summarizer(llm=mock_llm)
    summary = summarizer.summarize_document("Long text here...")
    assert len(summary) > 0
    mock_llm.complete.assert_called_once()


def test_summarize_document_returns_string():
    mock_llm = MagicMock()
    mock_llm.complete.return_value = MagicMock(text="A concise summary of the content.")
    summarizer = Summarizer(llm=mock_llm)
    result = summarizer.summarize_document("Some document text that needs summarizing.")
    assert isinstance(result, str)
    assert result == "A concise summary of the content."


def test_summarize_document_truncates_long_text():
    """Text longer than 8000 chars should be truncated before sending to LLM."""
    mock_llm = MagicMock()
    mock_llm.complete.return_value = MagicMock(text="Summary of truncated text.")
    summarizer = Summarizer(llm=mock_llm)
    long_text = "x" * 20000
    summarizer.summarize_document(long_text)
    called_prompt = mock_llm.complete.call_args[0][0]
    # The prompt should not contain more than 8000 chars of input text
    assert len(called_prompt) < 20000 + 200  # original text + some prompt overhead
    assert "x" * 8001 not in called_prompt


# ---------------------------------------------------------------------------
# test_generate_chunk_summaries
# ---------------------------------------------------------------------------

def test_generate_chunk_summaries():
    mock_llm = MagicMock()
    mock_llm.complete.return_value = MagicMock(text="Chunk summary.")
    nodes = [MagicMock(text="Content 1", id_="1"), MagicMock(text="Content 2", id_="2")]
    summarizer = Summarizer(llm=mock_llm)
    summaries = summarizer.summarize_chunks(nodes)
    assert len(summaries) == 2
    assert "1" in summaries and "2" in summaries


def test_summarize_chunks_returns_dict():
    mock_llm = MagicMock()
    mock_llm.complete.return_value = MagicMock(text="One-sentence summary.")
    nodes = [MagicMock(text="Text A", id_="node-a")]
    summarizer = Summarizer(llm=mock_llm)
    result = summarizer.summarize_chunks(nodes)
    assert isinstance(result, dict)
    assert result["node-a"] == "One-sentence summary."


def test_summarize_chunks_calls_llm_per_node():
    mock_llm = MagicMock()
    mock_llm.complete.return_value = MagicMock(text="Summary.")
    nodes = [
        MagicMock(text="Node 1 text", id_="id1"),
        MagicMock(text="Node 2 text", id_="id2"),
        MagicMock(text="Node 3 text", id_="id3"),
    ]
    summarizer = Summarizer(llm=mock_llm)
    summarizer.summarize_chunks(nodes)
    assert mock_llm.complete.call_count == 3


def test_summarize_chunks_empty_list():
    mock_llm = MagicMock()
    summarizer = Summarizer(llm=mock_llm)
    result = summarizer.summarize_chunks([])
    assert result == {}
    mock_llm.complete.assert_not_called()


# ---------------------------------------------------------------------------
# test_generate_qa_pairs
# ---------------------------------------------------------------------------

def test_generate_qa_pairs():
    mock_llm = MagicMock()
    mock_llm.complete.return_value = MagicMock(
        text="Q: What is X?\nA: X is Y.\nQ: How does Z work?\nA: Z works by..."
    )
    summarizer = Summarizer(llm=mock_llm)
    qa_pairs = summarizer.generate_qa_pairs("Some text")
    assert len(qa_pairs) == 2
    assert qa_pairs[0]["question"] == "What is X?"


def test_generate_qa_pairs_structure():
    mock_llm = MagicMock()
    mock_llm.complete.return_value = MagicMock(
        text="Q: What is Python?\nA: Python is a programming language.\nQ: What is a list?\nA: A list is a collection."
    )
    summarizer = Summarizer(llm=mock_llm)
    qa_pairs = summarizer.generate_qa_pairs("Python programming text.")
    assert len(qa_pairs) == 2
    for pair in qa_pairs:
        assert "question" in pair
        assert "answer" in pair


def test_generate_qa_pairs_answer_content():
    mock_llm = MagicMock()
    mock_llm.complete.return_value = MagicMock(
        text="Q: What is X?\nA: X is Y.\nQ: How does Z work?\nA: Z works by doing things."
    )
    summarizer = Summarizer(llm=mock_llm)
    qa_pairs = summarizer.generate_qa_pairs("Some text")
    assert qa_pairs[0]["answer"] == "X is Y."
    assert qa_pairs[1]["question"] == "How does Z work?"
    assert qa_pairs[1]["answer"] == "Z works by doing things."


def test_generate_qa_pairs_empty_response():
    """If LLM returns no Q:/A: lines, return an empty list."""
    mock_llm = MagicMock()
    mock_llm.complete.return_value = MagicMock(text="No valid pairs here.")
    summarizer = Summarizer(llm=mock_llm)
    qa_pairs = summarizer.generate_qa_pairs("Some text")
    assert qa_pairs == []


def test_generate_qa_pairs_calls_llm_once():
    mock_llm = MagicMock()
    mock_llm.complete.return_value = MagicMock(text="Q: A?\nA: B.")
    summarizer = Summarizer(llm=mock_llm)
    summarizer.generate_qa_pairs("Any text")
    mock_llm.complete.assert_called_once()


# ---------------------------------------------------------------------------
# test_parse_qa (internal helper via public interface)
# ---------------------------------------------------------------------------

def test_parse_qa_strips_whitespace():
    mock_llm = MagicMock()
    mock_llm.complete.return_value = MagicMock(
        text="Q:  What is whitespace?  \nA:  It is space.  "
    )
    summarizer = Summarizer(llm=mock_llm)
    qa_pairs = summarizer.generate_qa_pairs("text")
    assert qa_pairs[0]["question"] == "What is whitespace?"
    assert qa_pairs[0]["answer"] == "It is space."
