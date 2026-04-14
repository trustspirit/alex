from __future__ import annotations

import time
import logging

logger = logging.getLogger(__name__)


def with_retry(fn, max_retries: int = 3, base_delay: float = 1.0):
    """Execute *fn* with exponential backoff retry.

    Parameters
    ----------
    fn:
        A zero-argument callable to execute.
    max_retries:
        Maximum number of retries after the initial attempt.
    base_delay:
        Base delay in seconds; doubled after each failed attempt.

    Returns
    -------
    object
        Whatever *fn* returns on success.

    Raises
    ------
    Exception
        Re-raises the last exception after all retries are exhausted.
    """
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception as e:
            if attempt == max_retries:
                raise
            delay = base_delay * (2 ** attempt)
            logger.warning(
                "Attempt %d failed: %s. Retrying in %.1fs...",
                attempt + 1, e, delay,
            )
            time.sleep(delay)
