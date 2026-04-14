from __future__ import annotations

import logging
import os
import tempfile
from urllib.parse import parse_qs, urlparse

from backend.ingestion.loaders.base import LoadResult
from backend.ingestion.loaders.document import Document

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional imports – wrap in try/except so missing libraries don't crash
# at import time.  Imported at module level so tests can patch them.
# ---------------------------------------------------------------------------

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except Exception:
    YouTubeTranscriptApi = None  # type: ignore[assignment,misc]

try:
    import yt_dlp
except Exception:
    yt_dlp = None  # type: ignore[assignment]

try:
    import openai
except Exception:
    openai = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Module-level helper functions (outside class for testability)
# ---------------------------------------------------------------------------

def download_audio(video_url: str, output_dir: str) -> str:
    """Download audio from *video_url* using yt-dlp.

    Returns the path to the downloaded audio file.
    """
    if yt_dlp is None:
        raise ImportError("yt_dlp is not installed")

    output_template = os.path.join(output_dir, "audio.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

    audio_path = os.path.join(output_dir, "audio.mp3")
    if not os.path.exists(audio_path):
        # Search for any downloaded audio file
        for fname in os.listdir(output_dir):
            if fname.startswith("audio."):
                audio_path = os.path.join(output_dir, fname)
                break

    return audio_path


def transcribe_audio(audio_path: str, api_key: str) -> str:
    """Transcribe *audio_path* using the OpenAI GPT-4o Transcription API.

    Returns the transcribed text string.
    """
    if openai is None:
        raise ImportError("openai is not installed")

    client = openai.OpenAI(api_key=api_key)
    with open(audio_path, "rb") as f:
        response = client.audio.transcriptions.create(
            file=f,
            model="gpt-4o-transcribe",
            response_format="text",
        )
    return response


# ---------------------------------------------------------------------------
# YoutubeLoader
# ---------------------------------------------------------------------------

class YoutubeLoader:
    """2-tier YouTube loader: Transcript API → GPT-4o transcription (fallback)."""

    def __init__(self, openai_api_key: str = "") -> None:
        self._openai_api_key = openai_api_key

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, url: str) -> LoadResult:
        """Load transcript for the YouTube video at *url*.

        Tries tiers in order:
        1. YouTube Transcript API (free, fast)
        2. GPT-4o audio transcription via yt-dlp + OpenAI API

        Raises RuntimeError when all tiers fail.
        """
        video_id = self._extract_video_id(url)

        # --- Tier 1: YouTube Transcript API ---
        try:
            if YouTubeTranscriptApi is None:
                raise ImportError("youtube_transcript_api is not installed")
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            documents = self._transcript_to_documents(transcript_list, url)
            logger.debug("Transcript API succeeded for %s", url)
            return LoadResult(
                documents=documents,
                fallback_used=False,
                fallback_warning=None,
                has_structure=False,
            )
        except Exception as exc:
            logger.warning("Transcript API failed (%s), trying GPT-4o transcription…", exc)

        # --- Tier 2: GPT-4o transcription ---
        return self._fallback_transcribe(url)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_video_id(self, url: str) -> str:
        """Extract the YouTube video ID from a URL.

        Handles:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        """
        parsed = urlparse(url)

        if parsed.hostname in ("youtu.be",):
            # Short URL: path is "/VIDEO_ID"
            return parsed.path.lstrip("/")

        if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
            query_params = parse_qs(parsed.query)
            video_ids = query_params.get("v", [])
            if video_ids:
                return video_ids[0]

        raise ValueError(f"Cannot extract video ID from URL: {url}")

    def _format_timestamp(self, seconds: float) -> str:
        """Convert *seconds* to a human-readable timestamp string.

        Examples:
        - 0   → "0:00"
        - 83  → "1:23"
        - 3750 → "1:02:30"
        """
        total_seconds = int(seconds)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, secs = divmod(remainder, 60)

        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"

    def _transcript_to_documents(
        self, transcript_list: list, url: str
    ) -> list:
        """Convert a list of transcript entries to LlamaIndex Documents.

        Each entry has keys: "text", "start", "duration".
        The full transcript is joined into a single document with inline
        timestamps, e.g. "[0:00] Hello everyone\n[0:02] Today we discuss..."
        """
        lines: list[str] = []
        for entry in transcript_list:
            ts = self._format_timestamp(entry["start"])
            text = entry["text"].strip()
            lines.append(f"[{ts}] {text}")

        full_text = "\n".join(lines)
        doc = Document(
            text=full_text,
            metadata={
                "source": url,
                "type": "youtube",
                "method": "transcript_api",
            },
        )
        return [doc]

    def _fallback_transcribe(self, url: str) -> LoadResult:
        """Download audio and transcribe with GPT-4o.

        Returns a LoadResult with fallback_used=True and the Korean warning
        message.
        """
        warning = (
            "자막이 없는 영상입니다. 음성 인식으로 처리했으며, 정확도가 다소 낮을 수 있습니다."
        )
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                audio_path = download_audio(url, tmp_dir)
                text = transcribe_audio(audio_path, self._openai_api_key)

            doc = Document(
                text=text,
                metadata={
                    "source": url,
                    "type": "youtube",
                    "method": "gpt-4o-transcribe",
                },
            )
            logger.warning(warning)
            return LoadResult(
                documents=[doc],
                fallback_used=True,
                fallback_warning=warning,
                has_structure=False,
            )
        except Exception as exc:
            logger.error("GPT-4o transcription also failed (%s).", exc)
            raise RuntimeError(
                f"YouTube 로더의 모든 방법이 실패했습니다: {url}. "
                "Transcript API와 GPT-4o 음성 인식 모두 사용할 수 없습니다."
            ) from exc
