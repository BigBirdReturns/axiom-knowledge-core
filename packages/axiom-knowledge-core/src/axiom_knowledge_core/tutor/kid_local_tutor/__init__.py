"""
Kid‑Safe Local AI Tutor package.

This package exposes the core modules needed to build a local educational assistant.  See
`README.md` for high‑level documentation and usage instructions.
"""

# Re‑export key classes for convenience
from .rehydrate import TutorQnA
from .tutor_loop import TutorLoop
from .memory import MSONMemory
from .vector_store import VectorStore

__all__ = [
    "TutorQnA",
    "TutorLoop",
    "MSONMemory",
    "VectorStore",
]