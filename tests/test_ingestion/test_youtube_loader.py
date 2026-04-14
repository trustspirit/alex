from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from backend.ingestion.loaders.youtube_loader import (
    LoadResult,
    YoutubeLoader,
    download_audio,
    transcribe_audio,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_transcript_entries():
    return [
        {"text": "Hello everyone", "start": 0.0, "duration": 2.0},
        {"text": "Today we discuss AI", "start": 2.0, "duration": 3.0},
        {"text": "Let me show you", "start": 83.0, "duration": 2.5},
    ]


# ---------------------------------------------------------------------------
# Tier-1: Transcript API success
# ---------------------------------------------------------------------------

def test_load_with_transcript_api_success():
    """YouTubeTranscriptApi succeeds → documents with timestamps, no fallback."""
    entries = _make_transcript_entries()

    with patch(
        "backend.ingestion.loaders.youtube_loader.YouTubeTranscriptApi"
    ) as mock_api:
        mock_api.get_transcript.return_value = entries
        loader = YoutubeLoader()
        result = loader.load("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    assert isinstance(result, LoadResult)
    assert result.fallback_used is False
    assert result.fallback_warning is None
    assert result.has_structure is False
    assert len(result.documents) > 0

    # Documents should contain timestamped text
    combined_text = " ".join(doc.text for doc in result.documents)
    assert "[0:00]" in combined_text
    assert "Hello everyone" in combined_text


# ---------------------------------------------------------------------------
# Tier-2: Transcript API fails → GPT-4o transcription fallback
# ---------------------------------------------------------------------------

def test_load_falls_back_to_whisper():
    """Transcript API raises → fallback to GPT-4o transcription."""
    with patch(
        "backend.ingestion.loaders.youtube_loader.YouTubeTranscriptApi"
    ) as mock_api, patch(
        "backend.ingestion.loaders.youtube_loader.download_audio"
    ) as mock_download, patch(
        "backend.ingestion.loaders.youtube_loader.transcribe_audio"
    ) as mock_transcribe:

        mock_api.get_transcript.side_effect = Exception("No transcript available")
        mock_download.return_value = "/tmp/audio.mp3"
        mock_transcribe.return_value = "This is the transcribed audio content."

        loader = YoutubeLoader(openai_api_key="test-key")
        result = loader.load("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    assert result.fallback_used is True
    assert result.fallback_warning is not None
    assert "음성 인식" in result.fallback_warning
    assert len(result.documents) > 0
    assert result.documents[0].text == "This is the transcribed audio content."


# ---------------------------------------------------------------------------
# _extract_video_id
# ---------------------------------------------------------------------------

def test_extract_video_id_youtube_com():
    """Standard YouTube URL → correct video ID."""
    loader = YoutubeLoader()
    video_id = loader._extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert video_id == "dQw4w9WgXcQ"


def test_extract_video_id_youtu_be():
    """Short YouTube URL → correct video ID."""
    loader = YoutubeLoader()
    video_id = loader._extract_video_id("https://youtu.be/dQw4w9WgXcQ")
    assert video_id == "dQw4w9WgXcQ"


def test_extract_video_id_youtube_com_with_extra_params():
    """YouTube URL with extra query params → correct video ID."""
    loader = YoutubeLoader()
    video_id = loader._extract_video_id(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s&list=PLxxx"
    )
    assert video_id == "dQw4w9WgXcQ"


# ---------------------------------------------------------------------------
# _format_timestamp
# ---------------------------------------------------------------------------

def test_format_timestamp():
    """Various seconds values → expected timestamp strings."""
    loader = YoutubeLoader()
    assert loader._format_timestamp(0) == "0:00"
    assert loader._format_timestamp(83) == "1:23"
    assert loader._format_timestamp(3750) == "1:02:30"


def test_format_timestamp_minutes_only():
    """Exactly 60 seconds → '1:00'."""
    loader = YoutubeLoader()
    assert loader._format_timestamp(60) == "1:00"


def test_format_timestamp_large_value():
    """3600 seconds → '1:00:00'."""
    loader = YoutubeLoader()
    assert loader._format_timestamp(3600) == "1:00:00"


# ---------------------------------------------------------------------------
# _transcript_to_documents
# ---------------------------------------------------------------------------

def test_transcript_to_documents_includes_timestamps():
    """Transcript entries → Document with bracketed timestamps in text."""
    loader = YoutubeLoader()
    entries = [
        {"text": "Hello everyone", "start": 0.0, "duration": 2.0},
        {"text": "Today we discuss", "start": 2.0, "duration": 3.0},
    ]
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    docs = loader._transcript_to_documents(entries, url)

    assert len(docs) > 0
    combined = " ".join(doc.text for doc in docs)
    assert "[0:00]" in combined
    assert "Hello everyone" in combined
    assert "[0:02]" in combined
    assert "Today we discuss" in combined


def test_transcript_to_documents_metadata():
    """Documents have correct metadata keys."""
    loader = YoutubeLoader()
    entries = [{"text": "Test text", "start": 0.0, "duration": 1.0}]
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    docs = loader._transcript_to_documents(entries, url)

    for doc in docs:
        assert doc.metadata["source"] == url
        assert doc.metadata["type"] == "youtube"
        assert doc.metadata["method"] == "transcript_api"


# ---------------------------------------------------------------------------
# metadata on fallback documents
# ---------------------------------------------------------------------------

def test_fallback_documents_have_correct_metadata():
    """Fallback documents should have method='gpt-4o-transcribe' in metadata."""
    with patch(
        "backend.ingestion.loaders.youtube_loader.YouTubeTranscriptApi"
    ) as mock_api, patch(
        "backend.ingestion.loaders.youtube_loader.download_audio"
    ) as mock_download, patch(
        "backend.ingestion.loaders.youtube_loader.transcribe_audio"
    ) as mock_transcribe:

        mock_api.get_transcript.side_effect = Exception("No transcript")
        mock_download.return_value = "/tmp/audio.mp3"
        mock_transcribe.return_value = "Transcribed content here."

        loader = YoutubeLoader(openai_api_key="test-key")
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        result = loader.load(url)

    for doc in result.documents:
        assert doc.metadata["source"] == url
        assert doc.metadata["type"] == "youtube"
        assert doc.metadata["method"] == "gpt-4o-transcribe"
