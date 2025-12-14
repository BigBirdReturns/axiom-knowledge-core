"""
rehydrate.py
============

This module implements the retrieval‑augmented generation (RAG) pipeline used
by the local tutor.  The core idea is to retrieve relevant facts from the
vector store, rehydrate them into context for the language model, and then
ask the model to produce an answer.  The `TutorQnA` class encapsulates this
behaviour.

The implementation uses a local large language model via `llama‑cpp‑python`.
If that library (and a compatible model) are not available, it will fall
back to returning a canned response.  Users should customise this behaviour
to integrate other local LLMs or remote API calls if desired.
"""

from __future__ import annotations

import os
from typing import Iterable, List, Tuple

try:
    from llama_cpp import Llama
except ImportError:  # pragma: no cover - fallback when llama_cpp is unavailable
    Llama = None  # type: ignore

from .vector_store import VectorStore, SearchResult
from .utils import format_prompt
from .safety import filter_response


class TutorQnA:
    """High‑level Q&A interface combining retrieval and language model inference.

    Parameters
    ----------
    vector_store: VectorStore
        The vector store used to retrieve relevant context paragraphs.
    llm_path: str
        Path to the `.gguf` model file for `llama‑cpp‑python`.  If the file does
        not exist or `llama_cpp` is not installed, fallback mode will be used.
    system_prompt: str, optional
        Additional system instructions to prepend to each LLM call.  If not
        provided, a default instruction promoting simple, safe, child‑friendly
        responses will be used.
    persona: str, optional
        A persona string describing how the assistant should behave (e.g.
        “You are a patient third‑grade teacher”).
    """

    def __init__(self, vector_store: VectorStore, llm_path: str,
                 system_prompt: str | None = None,
                 persona: str | None = None) -> None:
        self.vector_store = vector_store
        self.system_prompt = system_prompt or (
            "You are a helpful educational assistant. Answer clearly, politely, and truthfully. "
            "Refuse to answer inappropriate questions and never use profanity."
        )
        self.persona = persona or "You are a gentle tutor speaking to a young learner."
        # Load local LLM
        if Llama is not None and os.path.exists(llm_path):
            try:
                self.llm = Llama(model_path=llm_path, n_ctx=2048)
            except Exception as exc:
                print(f"[rehydrate] Warning: failed to load LLM from {llm_path}: {exc}")
                self.llm = None
        else:
            if Llama is None:
                print("[rehydrate] llama_cpp not available; using fallback responses.")
            else:
                print(f"[rehydrate] Model file not found: {llm_path}; using fallback responses.")
            self.llm = None

    def answer(self, query: str, k: int = 3) -> Tuple[str, List[SearchResult]]:
        """Answer a question using retrieval‑augmented generation.

        This function embeds the query, retrieves the top‑`k` most similar
        context chunks from the vector store, constructs a prompt for the LLM
        using `utils.format_prompt`, and generates a response.  The response
        passes through a safety filter before being returned.

        Parameters
        ----------
        query: str
            The user’s question.
        k: int
            Number of context passages to retrieve.

        Returns
        -------
        tuple
            A pair consisting of the (possibly filtered) answer string and a
            list of `SearchResult` objects representing the retrieved
            documents (useful for citation in the UI).
        """
        # Retrieve context from vector store
        results: List[SearchResult] = self.vector_store.query(query, k=k)
        context_passages = [r.document for r in results]
        # Format prompt for the LLM
        prompt = format_prompt(query, context_passages, persona=self.persona,
                               system_instructions=self.system_prompt)
        # Generate answer
        if self.llm is not None:
            # The llama_cpp.Llama interface expects a single string prompt and returns a
            # dictionary containing the generated text under the 'choices' key.
            try:
                response = self.llm(prompt, max_tokens=256, stop=["<|user|>"])
                raw_text = response["choices"][0]["text"].strip()
            except Exception as exc:
                print(f"[rehydrate] Error during LLM inference: {exc}")
                raw_text = "I'm sorry, I encountered an error while thinking about that."
        else:
            # Fallback behaviour when no LLM is available
            raw_text = (
                "I'm sorry, I cannot answer that right now because the language model "
                "is unavailable. Please try again after the model is installed."
            )
        # Apply safety filter
        safe_text = filter_response(raw_text)
        return safe_text, results


__all__ = ["TutorQnA"]