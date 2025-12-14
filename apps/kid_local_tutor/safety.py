"""
safety.py
=========

Basic content moderation utilities for the local tutor.  These functions
implement a simple keyword blacklist to detect and remove inappropriate
language from both the assistant’s responses and the child’s inputs.  The
filtering is intentionally conservative: if a banned word is present,
the offending term is replaced with a censored token (e.g. "🤐") and a
warning can be logged.  More sophisticated moderation models can be added
later (for example using a small hate speech classifier running locally).
"""

from __future__ import annotations

import re
from typing import List


# A small list of banned words/phrases.  Extend this list as needed.  All
# matches are case‑insensitive.  Words shorter than 3 characters are not
# included because of false positives.  Do not include regex special
# characters unless intended.
_BANNED_WORDS: List[str] = [
    "fuck", "shit", "bitch", "asshole", "dick", "pussy", "porn", "sex",
    "nigger", "faggot", "whore", "rape", "kill", "suicide", "dead", "murder",
]


def _compile_pattern() -> re.Pattern[str]:
    escaped = [re.escape(word) for word in _BANNED_WORDS]
    pattern = r"(" + r"|".join(escaped) + r")"
    return re.compile(pattern, flags=re.IGNORECASE)


_BANNED_PATTERN = _compile_pattern()


def is_inappropriate(text: str) -> bool:
    """Return True if the text contains any banned words."""
    return bool(_BANNED_PATTERN.search(text))


def filter_response(text: str) -> str:
    """Replace banned words in a response with a censor token.

    The filter lowers the severity of offensive language by replacing banned
    terms with "🤐".  It does not remove the entire sentence to preserve
    context.  If no banned words are found, the text is returned unchanged.

    Parameters
    ----------
    text: str
        The assistant’s raw response.

    Returns
    -------
    str
        The filtered response.
    """
    return _BANNED_PATTERN.sub("🤐", text)


def filter_user_input(text: str) -> str:
    """Filter the child’s input for banned words.

    This can be used before processing user queries to refuse or
    sanitise inappropriate questions.  The current implementation simply
    censors banned words; for more nuanced control you can detect topics and
    respond with a refusal instead (see `is_inappropriate`).
    """
    return filter_response(text)


__all__ = ["is_inappropriate", "filter_response", "filter_user_input"]