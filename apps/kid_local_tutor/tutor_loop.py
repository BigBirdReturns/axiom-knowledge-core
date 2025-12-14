"""
tutor_loop.py
=============

The `TutorLoop` class implements an interactive loop for the voice‑based tutor.
It continually listens for user input, transcribes speech into text, filters
inappropriate content, queries the knowledge base via the retrieval pipeline,
and plays back the answer using text‑to‑speech.  It also logs all
interactions into the memory system for later review.

Because many embedded devices may not have full audio libraries installed,
this implementation degrades gracefully when audio support is missing.  It
checks for the availability of `whispercpp` and `piper_tts` modules.  If
either is missing, it falls back to reading input from the console and
printing responses.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Optional

try:
    from whispercpp import Whisper
except ImportError:
    Whisper = None  # type: ignore

try:
    import piper
except ImportError:
    piper = None  # type: ignore

import sounddevice as sd  # type: ignore
import numpy as np  # type: ignore

from .rehydrate import TutorQnA
from .vector_store import VectorStore
from .memory import MSONMemory, MemoryItem
from .safety import filter_user_input, is_inappropriate
from .language_utils import detect_language, translate_text


class TutorLoop:
    """Interactive loop for the offline voice tutor.

    Parameters
    ----------
    vector_store: VectorStore
        The vector store used for retrieval.
    llm_path: str
        Path to the quantised GGUF file used by the LLM.
    memory_path: str
        Path to the JSON file used for persistent memory.  If the file does
        not exist it will be created.
    whisper_model: str, optional
        Path to the Whisper model (e.g. `tiny.en.ggml.bin`).  Required only if
        audio transcription is enabled.  When not provided or when
        `whispercpp` is unavailable, the tutor will prompt for typed input
        instead of recording audio.
    piper_voice: str, optional
        Path to the Piper TTS voice (e.g. `en_US-amy-medium.onnx`).  Required
        for audio playback.  When not provided or when `piper` is unavailable,
        the tutor will print responses to the console.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        llm_path: str,
        memory_path: str | Path,
        whisper_model: Optional[str] = None,
        piper_voice: Optional[str] = None,
        default_language: str = "en",
    ) -> None:
        self.vector_store = vector_store
        self.qna = TutorQnA(vector_store, llm_path)
        self.memory = MSONMemory(memory_path)
        self.whisper_model_path = whisper_model
        self.piper_voice_path = piper_voice
        # Default language used for LLM queries and fallback translations
        self.default_language = default_language
        # Initialise STT and TTS engines if available
        if Whisper is not None and whisper_model:
            try:
                self.whisper = Whisper(model_path=whisper_model)
            except Exception as exc:
                print(f"[tutor_loop] Failed to load Whisper model: {exc}")
                self.whisper = None
        else:
            self.whisper = None
        if piper is not None and piper_voice:
            try:
                self.tts = piper.PiperVoice(piper_voice)
            except Exception as exc:
                print(f"[tutor_loop] Failed to load Piper voice: {exc}")
                self.tts = None
        else:
            self.tts = None

    def record_audio(self, duration: float = 5.0, samplerate: int = 16000) -> Optional[np.ndarray]:
        """Record audio from the microphone.

        Parameters
        ----------
        duration: float
            Duration of recording in seconds.
        samplerate: int
            Sample rate in Hz.

        Returns
        -------
        np.ndarray or None
            The recorded mono audio as a numpy array.  If recording fails or
            sounddevice is not available, returns `None`.
        """
        try:
            return sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='float32').flatten()
        except Exception as exc:
            print(f"[tutor_loop] Audio recording failed: {exc}")
            return None

    def transcribe_audio(self, audio_data: np.ndarray, samplerate: int = 16000) -> str:
        """Transcribe audio to text using Whisper.

        If the Whisper engine is not available, raises a RuntimeError.
        """
        if not self.whisper:
            raise RuntimeError("Whisper is not initialised. Cannot transcribe audio.")
        # whispercpp expects 16 kHz 16‑bit PCM; convert float32 to int16
        pcm = (audio_data * 32767.0).astype('int16')
        result = self.whisper.transcribe(pcm, samplerate)
        return result['text']

    def speak(self, text: str) -> None:
        """Speak a string aloud using Piper.

        If TTS is unavailable, print the text to the console instead.
        """
        if self.tts:
            try:
                audio = self.tts.text_to_audio(text)
                sd.play(audio, self.tts.sample_rate)
                sd.wait()
            except Exception as exc:
                print(f"[tutor_loop] Failed to speak: {exc}")
                print(text)
        else:
            print(f"Tutor: {text}")

    def run(self) -> None:
        """Enter the tutor interaction loop.

        In each iteration the tutor:
        1. Records or reads a question from the user.
        2. Filters the user input for inappropriate language.
        3. Calls the Q&A pipeline to generate an answer.
        4. Applies the safety filter to the answer.
        5. Logs the interaction into memory.
        6. Speaks or prints the answer.

        To quit the loop, press Ctrl+C.
        """
        print("[tutor_loop] Starting tutor. Press Ctrl+C to exit.")
        while True:
            try:
                # Step 1: get user input
                if self.whisper and self.tts:
                    print("Please speak your question...")
                    audio = self.record_audio()
                    if audio is None:
                        # Fallback to text input
                        text_input = input("You: ")
                    else:
                        text_input = self.transcribe_audio(audio)
                        print(f"You said: {text_input}")
                else:
                    # Text fallback
                    text_input = input("You: ")

                # Step 2: filter user input
                sanitized = filter_user_input(text_input)
                # Detect the language of the user input; default to English on error
                src_lang = detect_language(sanitized)
                if is_inappropriate(sanitized):
                    # Respond with refusal
                    response_text = (
                        "I'm sorry, I can't talk about that. Let's discuss something else."
                    )
                    # Record reflective memory
                    self.memory.add("reflective", MemoryItem(
                        id=f"reflective-{time.time()}",
                        content=response_text,
                        metadata={"trigger": text_input, "note": "user input inappropriate"}
                    ))
                else:
                    # Translate the query to the default language if required
                    translated_query = translate_text(sanitized, src_lang, self.default_language)
                    # Step 3: get answer from Q&A pipeline
                    response_text, search_results = self.qna.answer(translated_query)
                    # Translate the answer back to the source language
                    response_text = translate_text(response_text, self.default_language, src_lang)
                    # Step 4: memory logging
                    timestamp = time.time()
                    self.memory.add("working", MemoryItem(
                        id=f"question-{timestamp}",
                        content=sanitized,
                        metadata={"timestamp": timestamp, "type": "user_question", "language": src_lang}
                    ))
                    # Save retrieval context into persistent memory as well
                    for res in search_results:
                        self.memory.add("persistent", MemoryItem(
                            id=f"context-{timestamp}-{res.metadata.get('chunk_index', 0)}",
                            content=res.document,
                            metadata={"source": res.metadata.get("source"), "distance": res.distance}
                        ))
                    # Reflective memory stores AI rationale (simplified)
                    self.memory.add("reflective", MemoryItem(
                        id=f"answer-{timestamp}",
                        content=response_text,
                        metadata={"question": sanitized, "sources": [r.metadata for r in search_results], "language": src_lang}
                    ))
                    # Persist memory after each interaction
                    self.memory.save()
                # Step 5: speak or print answer
                self.speak(response_text)
            except KeyboardInterrupt:
                print("\n[tutor_loop] Exiting tutor loop.")
                break
            except Exception as exc:
                print(f"[tutor_loop] Unexpected error: {exc}")
                break