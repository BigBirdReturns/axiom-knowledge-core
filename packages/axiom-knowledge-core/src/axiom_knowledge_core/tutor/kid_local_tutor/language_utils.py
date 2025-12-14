"""
language_utils.py
==================

Utility functions for detecting the language of a user query and translating
between languages when needed.  These helpers are kept lightweight and have
graceful fallbacks so that the tutor can run even if optional multilingual
dependencies are not installed.  If translation packages are unavailable,
the functions simply return the input unchanged.

The default design assumes that most content will be in English but allows
parents to add support for other languages by installing the optional
`langdetect` and `argostranslate` packages.  See the project README for
instructions on how to download additional translation models.

Functions
---------
detect_language(text: str) -> str
    Attempt to identify the ISO 639‑1 code of the language used in a given
    string.  Returns ``"en"`` if detection fails or the detector is not
    available.

translate_text(text: str, src_lang: str, tgt_lang: str) -> str
    Translate a piece of text from one language to another using
    `argostranslate`.  If the translator or the required language pair is
    unavailable, the function falls back to returning the original text.

"""

from __future__ import annotations

from typing import Optional

try:
    # Optional dependency for language detection
    from langdetect import detect  # type: ignore
except ImportError:
    detect = None  # type: ignore

try:
    # Optional dependency for offline translation
    from argostranslate import package as _argo_package  # type: ignore
    from argostranslate import translate as _argo_translate  # type: ignore
except ImportError:
    _argo_package = None  # type: ignore
    _argo_translate = None  # type: ignore


def detect_language(text: str) -> str:
    """Identify the language of the given text.

    If the `langdetect` package is installed, this function attempts to
    determine the language code of ``text``.  Otherwise it defaults to
    returning ``"en"``.

    Parameters
    ----------
    text: str
        The text whose language should be detected.

    Returns
    -------
    str
        A two‑letter ISO 639‑1 language code.  Returns ``"en"`` if detection
        fails or the detector is unavailable.
    """
    if detect is None:
        return "en"
    try:
        lang = detect(text)
        # Some detectors return regional codes (e.g. 'zh-cn'); keep primary part
        if len(lang) > 2 and "-" in lang:
            lang = lang.split("-")[0]
        return lang
    except Exception:
        return "en"


def _ensure_package(src: str, tgt: str) -> bool:
    """Ensure that a translation package for a language pair is installed.

    Argos Translate uses translation packages for each language pair.  This
    helper checks whether a package exists for ``src``→``tgt`` and returns
    ``True`` if translation should be possible.  If packages are missing or
    ``argostranslate`` is not installed, it returns ``False``.
    """
    if _argo_package is None:
        return False
    try:
        installed = _argo_package.get_installed_packages()
    except Exception:
        return False
    for pkg in installed:
        if pkg.from_code == src and pkg.to_code == tgt:
            return True
    return False


def translate_text(text: str, src_lang: str, tgt_lang: str) -> str:
    """Translate text between languages using Argos Translate.

    Parameters
    ----------
    text: str
        The text to translate.
    src_lang: str
        ISO 639‑1 code of the source language.
    tgt_lang: str
        ISO 639‑1 code of the target language.

    Returns
    -------
    str
        The translated text, or the original ``text`` if translation could
        not be performed (due to missing packages or unsupported language
        pairs).
    """
    # No translation needed if languages match
    if not text:
        return text
    if src_lang == tgt_lang:
        return text
    if _argo_translate is None or not _ensure_package(src_lang, tgt_lang):
        # Translator not available or package missing
        return text
    try:
        return _argo_translate.translate(text, src_lang, tgt_lang)
    except Exception:
        # On failure, return original
        return text


__all__ = ["detect_language", "translate_text"]