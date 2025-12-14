"""
memory.py
==========

This module implements a simple memory subsystem inspired by the MSON (Multi‑Structured
Object Notebook) described in the project documentation.  It separates memory into
four categories:

* **working** – short‑term, in‑RAM context such as current conversation turns.
* **persistent** – long‑term knowledge extracted from documents and past dialogues.
* **reflective** – diary and rationale information explaining the system’s behaviour.
* **volatile** – transient data used for intermediate reasoning steps.

Each memory item is a small dictionary with an `id`, `content`, and arbitrary
`metadata`.  Metadata can include fields such as `timestamp`, `source`, `topic`,
`keywords`, or any other relevant tags.  The entire memory object can be serialised
to disk in JSON format.  Because this is a local‑first system, no network calls are
made.

Usage:

>>> mem = MSONMemory("data/memory.json")
>>> mem.add("working", {"id": "123", "content": "What is 2+2?", "metadata": {"topic": "math"}})
>>> mem.add("persistent", {"id": "doc:math_001", "content": "Two plus two equals four.", "metadata": {"source": "Textbook"}})
>>> mem.save()

You can search across memory categories using simple keyword matching.  For more
advanced retrieval, consider embedding the memory items and searching via
`vector_store.VectorStore`.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Iterable, Optional, Any


@dataclass
class MemoryItem:
    """Represents a single memory entry.

    Attributes:
        id: A unique string identifying the memory item.
        content: The textual content of the memory (question, answer, rationale, etc.).
        metadata: Arbitrary dictionary containing metadata such as timestamps,
            topics, keywords, sources or emotions.  Metadata should be JSON serialisable.
    """

    id: str
    content: str
    metadata: Dict[str, Any]


class MSONMemory:
    """Container for multiple categories of memory items.

    The memory is stored in a JSON file on disk.  It is organised into four
    categories: `working`, `persistent`, `reflective`, and `volatile`.  Each
    category holds a list of `MemoryItem` objects.  The design is simple and
    extensible: additional categories can be added by modifying `self._categories`.

    Parameters
    ----------
    path: str or Path
        Path to the JSON file used for persisting memory.  If the file exists
        it will be loaded automatically.  If it does not exist, a new file
        will be created when saving.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._categories: Dict[str, List[MemoryItem]] = {
            "working": [],
            "persistent": [],
            "reflective": [],
            "volatile": [],
        }
        # Load memory from disk if present
        if self.path.exists():
            self.load()

    def load(self) -> None:
        """Load memory from disk.

        If the file does not contain expected categories, they will be initialised.
        """
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for category in self._categories:
                items_data = data.get(category, [])
                self._categories[category] = [MemoryItem(**item) for item in items_data]
        except Exception as exc:
            # If loading fails, start with empty memory; log the error for debugging
            print(f"[memory] Warning: failed to load memory from {self.path}: {exc}")
            # leaving categories empty

    def save(self) -> None:
        """Serialise the memory to disk.

        This writes the internal state to JSON, overwriting the existing file.  The
        file is human‑readable and can be inspected for auditing.  If the parent
        directory does not exist, it will be created.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data: Dict[str, List[Dict[str, Any]]] = {}
        for category, items in self._categories.items():
            data[category] = [asdict(item) for item in items]
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add(self, category: str, item: MemoryItem) -> None:
        """Add a memory item to a category.

        Parameters
        ----------
        category: str
            One of "working", "persistent", "reflective", or "volatile".
        item: MemoryItem
            The memory item to add.  The item’s `id` should be unique across
            all categories; duplicate IDs are allowed but may cause confusion.
        """
        if category not in self._categories:
            raise ValueError(f"Unknown memory category '{category}'.")
        self._categories[category].append(item)

    def search(self, query: str, category: Optional[str] = None) -> Iterable[MemoryItem]:
        """Perform a naive keyword search over memory.

        This function performs a simple case‑insensitive substring match over
        memory items' `content` fields.  For advanced semantic search, use
        `vector_store.VectorStore` instead.

        Parameters
        ----------
        query: str
            The search string.
        category: str, optional
            If provided, restrict the search to a single category.

        Returns
        -------
        Iterable[MemoryItem]
            A generator yielding memory items that match the query.
        """
        query_lower = query.lower()
        categories = [category] if category else self._categories.keys()
        for cat in categories:
            for item in self._categories.get(cat, []):
                if query_lower in item.content.lower():
                    yield item

    def dump_summary(self) -> Dict[str, int]:
        """Return a summary of the number of items in each category.

        Returns
        -------
        dict
            Keys are category names and values are item counts.
        """
        return {cat: len(items) for cat, items in self._categories.items()}


__all__ = ["MemoryItem", "MSONMemory"]