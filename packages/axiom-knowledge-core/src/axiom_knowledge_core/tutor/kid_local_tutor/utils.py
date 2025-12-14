"""
utils.py
========

A collection of helper functions used throughout the local tutor project.  The
functions in this module perform mundane but essential tasks such as loading
documents, chunking text, formatting prompts for the language model, and
extracting simple keywords and summaries from text.  These utilities are kept
lightweight and have no external dependencies beyond the standard library
unless absolutely necessary.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterable, List, Tuple


def load_document(path: str | Path) -> str:
    """Load a text document into a single string.

    This function reads files with a `.txt` extension directly.  For PDF or
    other formats, it raises a `NotImplementedError` to encourage users to
    provide their own loader.  You may install and use libraries such as
    `pdfplumber` or `PyPDF2` to support PDFs; however, those are not included
    in the default requirements.  The function normalises newlines to `\n`.

    Parameters
    ----------
    path: str or Path
        Path to the document file.

    Returns
    -------
    str
        The entire contents of the document as a string.
    """
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".txt":
        with open(path, "r", encoding="utf-8") as f:
            return f.read().replace("\r\n", "\n").replace("\r", "\n")
    elif suffix == ".pdf":
        raise NotImplementedError(
            "PDF loading is not implemented in utils.load_document. "
            "Install a PDF parser (e.g. pdfplumber) and implement as needed."
        )
    else:
        raise NotImplementedError(
            f"Unsupported file extension '{suffix}'. Only .txt is supported by default."
        )


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
    """Split a long string into overlapping chunks.

    The resulting list contains segments of at most `chunk_size` tokens
    (approximate by word count).  Consecutive chunks overlap by `overlap`
    tokens to preserve context across chunk boundaries.  This simplistic
    function uses whitespace tokenisation; for more accurate splitting you
    should adapt it to your tokenizer.

    Parameters
    ----------
    text: str
        The input string to split.
    chunk_size: int
        Maximum number of words per chunk.
    overlap: int
        Number of words to overlap between consecutive chunks.

    Returns
    -------
    list of str
        A list of text chunks.
    """
    words = text.split()
    if chunk_size <= 0:
        return [text]
    chunks: List[str] = []
    i = 0
    while i < len(words):
        end = min(i + chunk_size, len(words))
        chunk = " ".join(words[i:end])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


def format_prompt(query: str, context: Iterable[str], persona: str = "You are a helpful tutor.",
                  system_instructions: str | None = None) -> str:
    """Combine system instructions, persona, retrieved context, and the user query into a prompt.

    The prompt structure used with the local LLM typically looks like:

    ```
    <|system|>
    [system instructions]
    <|persona|>
    [persona description]
    <|context|>
    [retrieved facts]
    <|user|>
    [user's question]
    <|assistant|>
    ```

    Not all LLMs require this exact formatting, but this helper provides a
    reasonable default that can be customised by passing in different
    `persona` and `system_instructions` strings.

    Parameters
    ----------
    query: str
        The user’s question.
    context: Iterable[str]
        A sequence of retrieved documents or facts to ground the answer.
    persona: str
        A short description of the tutor’s behaviour (e.g. “You are a kind,
        patient elementary school teacher.”).
    system_instructions: str, optional
        Additional low‑level instructions for the LLM (e.g. “Never produce
        profanity. Answer clearly and concisely.”).  If `None`, a generic
        instruction will be used.

    Returns
    -------
    str
        The concatenated prompt ready for the language model.
    """
    system_instructions = system_instructions or (
        "You are running on an offline device. Do not mention the internet. "
        "Avoid inappropriate topics and explain concepts in simple terms."
    )
    prompt_parts = [
        "<|system|>\n",
        system_instructions.strip(),
        "\n<|persona|>\n",
        persona.strip(),
        "\n<|context|>\n",
    ]
    # Join context passages with separator
    prompt_parts.append("\n\n".join([c.strip() for c in context]))
    prompt_parts.extend([
        "\n<|user|>\n",
        query.strip(),
        "\n<|assistant|>\n",
    ])
    return "".join(prompt_parts)


def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
    """Extract simple keywords from a string using a frequency heuristic.

    This function counts the frequency of alphanumeric words (excluding common
    stopwords) and returns the most frequent unique tokens up to
    `max_keywords`.  It is designed to be lightweight and not depend on
    external NLP libraries.  For more sophisticated keyword extraction,
    consider using libraries such as spaCy or nltk.

    Parameters
    ----------
    text: str
        Input text to extract keywords from.
    max_keywords: int
        Maximum number of keywords to return.

    Returns
    -------
    list of str
        A list of keyword strings sorted by decreasing frequency.
    """
    # A simple list of stopwords; extend as needed
    stopwords = set([
        "the", "and", "to", "of", "a", "in", "is", "it", "that", "for",
        "on", "with", "as", "this", "be", "are", "was", "by", "an",
    ])
    # Extract words (letters and numbers)
    tokens = re.findall(r"[A-Za-z0-9']+", text.lower())
    freq: dict[str, int] = {}
    for tok in tokens:
        if tok not in stopwords and len(tok) > 2:
            freq[tok] = freq.get(tok, 0) + 1
    # Sort tokens by frequency then alphabetically
    sorted_tokens = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
    return [tok for tok, count in sorted_tokens[:max_keywords]]


def generate_summary(text: str, max_sentences: int = 2) -> str:
    """Generate a naïve summary by selecting the first sentences.

    This helper simply splits the input into sentences using a period and
    returns the first `max_sentences`.  It does not perform any semantic
    analysis.  For a more informative summary, you may integrate a small
    summarisation model or algorithm.

    Parameters
    ----------
    text: str
        The text to summarise.
    max_sentences: int
        The maximum number of sentences to include in the summary.

    Returns
    -------
    str
        The summary consisting of the first `max_sentences` sentences.
    """
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join(sentences[:max_sentences])