from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

SUMMARY_PROMPT = (
    "Summarize the following text in 2-3 sentences. Focus on key concepts.\n\n"
    "Text:\n{text}\n\nSummary:"
)

CHUNK_SUMMARY_PROMPT = (
    "Write a one-sentence summary of this text chunk:\n\n{text}\n\nSummary:"
)

QA_PROMPT = (
    "Generate 2-3 question-answer pairs from this text. "
    "Format: Q: [question]\\nA: [answer]\n\nText:\n{text}\n\nQ&A:"
)

# Maximum characters of document text sent to LLM for full-document summary.
_MAX_DOC_CHARS = 8000


class Summarizer:
    """LLM-based summarizer for documents, chunks, and Q&A pair generation."""

    def __init__(self, llm) -> None:
        self._llm = llm

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def summarize_document(self, full_text: str) -> str:
        """Generate a 2-3 sentence summary of the entire document.

        Parameters
        ----------
        full_text:
            Raw text of the document.  Truncated to 8 000 characters before
            being sent to the LLM.

        Returns
        -------
        str
            The summary produced by the LLM.
        """
        truncated = full_text[:_MAX_DOC_CHARS]
        prompt = SUMMARY_PROMPT.format(text=truncated)
        response = self._llm.complete(prompt)
        summary: str = response.text.strip()
        logger.debug("Document summary generated (%d chars).", len(summary))
        return summary

    def summarize_chunks(self, nodes: list) -> dict[str, str]:
        """Generate a one-line summary per chunk node.

        Parameters
        ----------
        nodes:
            List of node objects, each with ``.text`` and ``.id_`` attributes.

        Returns
        -------
        dict[str, str]
            Mapping of ``node.id_`` → one-sentence summary string.
        """
        summaries: dict[str, str] = {}
        for node in nodes:
            prompt = CHUNK_SUMMARY_PROMPT.format(text=node.text)
            response = self._llm.complete(prompt)
            summaries[node.id_] = response.text.strip()
        logger.debug("Chunk summaries generated for %d nodes.", len(summaries))
        return summaries

    def generate_qa_pairs(self, text: str) -> list[dict[str, str]]:
        """Generate Q&A pairs from *text*.

        Parameters
        ----------
        text:
            Source text from which questions and answers are derived.

        Returns
        -------
        list[dict[str, str]]
            A list of ``{"question": ..., "answer": ...}`` dictionaries.
            Returns an empty list when no valid Q:/A: pairs are found in the
            LLM response.
        """
        prompt = QA_PROMPT.format(text=text)
        response = self._llm.complete(prompt)
        qa_pairs = self._parse_qa(response.text)
        logger.debug("Generated %d Q&A pairs.", len(qa_pairs))
        return qa_pairs

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _parse_qa(self, raw: str) -> list[dict[str, str]]:
        """Parse ``Q: ...\nA: ...`` formatted text into a list of dicts."""
        pairs: list[dict[str, str]] = []
        current_question: str | None = None
        current_answer: str | None = None

        for line in raw.splitlines():
            stripped = line.strip()
            if stripped.startswith("Q:"):
                # If we have a pending pair, save it first
                if current_question is not None and current_answer is not None:
                    pairs.append(
                        {"question": current_question, "answer": current_answer}
                    )
                current_question = stripped[2:].strip()
                current_answer = None
            elif stripped.startswith("A:") and current_question is not None:
                current_answer = stripped[2:].strip()

        # Save the last pending pair
        if current_question is not None and current_answer is not None:
            pairs.append({"question": current_question, "answer": current_answer})

        return pairs
