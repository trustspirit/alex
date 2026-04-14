from __future__ import annotations

import logging
import os
import re

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional tiktoken import — wrapped so missing library doesn't crash at
# import time.
# ---------------------------------------------------------------------------

try:
    import tiktoken as _tiktoken  # type: ignore[import]
    _TIKTOKEN_AVAILABLE = True
except Exception:
    _tiktoken = None  # type: ignore[assignment]
    _TIKTOKEN_AVAILABLE = False


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """Count the number of tokens in *text* using tiktoken.

    Parameters
    ----------
    text:
        The text to tokenize.
    model:
        The model name used to select the tiktoken encoding.  Defaults to
        ``"gpt-4o"``.  Falls back to ``cl100k_base`` when the model is not
        recognised or tiktoken is unavailable.

    Returns
    -------
    int
        Number of tokens.
    """
    if not _TIKTOKEN_AVAILABLE or _tiktoken is None:
        # Rough fallback: split on whitespace
        return len(text.split())

    try:
        enc = _tiktoken.encoding_for_model(model)
    except KeyError:
        logger.debug(
            "tiktoken: model '%s' not found, falling back to cl100k_base.", model
        )
        enc = _tiktoken.get_encoding("cl100k_base")

    return len(enc.encode(text))


def extract_metadata(documents: list, source_path: str, source_type: str) -> dict:
    """Extract a metadata dictionary from a list of documents.

    Parameters
    ----------
    documents:
        List of document objects, each with a ``.text`` attribute.
    source_path:
        Filesystem path (or URL) where the source was loaded from.
    source_type:
        Type identifier for the source (e.g. ``"pdf"``, ``"markdown"``).

    Returns
    -------
    dict
        Dictionary with keys: ``title``, ``source_path``, ``source_type``,
        ``token_count``.
    """
    full_text = "\n".join(doc.text for doc in documents)
    title = _extract_title(documents, source_path)
    token_count = count_tokens(full_text)

    return {
        "title": title,
        "source_path": source_path,
        "source_type": source_type,
        "token_count": token_count,
    }


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _extract_title(documents: list, source_path: str) -> str:
    """Try to extract the title from the first Markdown heading in *documents*.

    Falls back to deriving a human-readable name from the *source_path*
    filename when no heading is found.

    Parameters
    ----------
    documents:
        List of document objects with ``.text`` attribute.
    source_path:
        Filesystem path used for the filename fallback.

    Returns
    -------
    str
        The extracted or derived title string.
    """
    # Walk through documents in order and look for the first heading line
    heading_re = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)
    for doc in documents:
        match = heading_re.search(doc.text)
        if match:
            return match.group(1).strip()

    # Fallback: convert filename to title
    filename = os.path.splitext(os.path.basename(source_path))[0]
    # Replace hyphens and underscores with spaces, then title-case
    title = filename.replace("-", " ").replace("_", " ").title()
    return title
