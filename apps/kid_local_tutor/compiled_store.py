"""compiled_store.py

Compiled-substrate retrieval for Kid Local Tutor.

This module allows the tutor runtime to pull context from AXIOM compiled
artifacts (concepts/relations/provenance) instead of a vector store.

It intentionally keeps retrieval deterministic and lightweight so it can run
on constrained hardware.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from .vector_store import SearchResult


def _tokenize(text: str) -> List[str]:
    text = (text or "").lower()
    return [t for t in re.split(r"[^a-z0-9]+", text) if len(t) >= 3]


@dataclass(frozen=True)
class CompiledConcept:
    id: str
    title: str
    summary: str | None
    tags: List[str]


class CompiledStore:
    """Read-only retriever over a compiled AXIOM artifact directory."""

    def __init__(self, compiled_dir: str | Path) -> None:
        self.compiled_dir = Path(compiled_dir)
        self.concepts = self._load_concepts(self.compiled_dir / "concepts.jsonl")
        self.provenance = self._load_provenance(self.compiled_dir / "provenance.jsonl")

        # Pre-tokenize for deterministic matching.
        self._concept_tokens: Dict[str, set[str]] = {}
        for c in self.concepts:
            toks = set(_tokenize(c.title) + _tokenize(c.summary or ""))
            self._concept_tokens[c.id] = toks

    @staticmethod
    def _load_concepts(path: Path) -> List[CompiledConcept]:
        out: List[CompiledConcept] = []
        if not path.exists():
            return out
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                d = json.loads(line)
                out.append(
                    CompiledConcept(
                        id=d["id"],
                        title=d.get("title", ""),
                        summary=d.get("summary"),
                        tags=list(d.get("tags", []) or []),
                    )
                )
        return out

    @staticmethod
    def _load_provenance(path: Path) -> Dict[str, List[Dict[str, Any]]]:
        """Map target_id -> list of provenance entries."""
        out: Dict[str, List[Dict[str, Any]]] = {}
        if not path.exists():
            return out
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                d = json.loads(line)
                target = d.get("target_id")
                if not target:
                    continue
                out.setdefault(target, []).append(d)
        return out

    def query(self, query: str, k: int = 3) -> List[SearchResult]:
        """Deterministic keyword overlap retrieval.

        Returns SearchResult objects so the rest of the tutor pipeline can stay
        unchanged.
        """
        q_tokens = set(_tokenize(query))
        if not q_tokens:
            return []

        scored: List[tuple[float, CompiledConcept]] = []
        for c in self.concepts:
            ct = self._concept_tokens.get(c.id, set())
            overlap = len(q_tokens & ct)
            if overlap == 0:
                continue
            # Prefer shorter concepts very slightly to reduce spam.
            denom = max(6, len(ct))
            score = overlap / denom
            scored.append((score, c))

        scored.sort(key=lambda t: t[0], reverse=True)
        top = scored[:k]

        results: List[SearchResult] = []
        for rank, (score, c) in enumerate(top, start=1):
            prov_entries = self.provenance.get(c.id, [])
            citation_lines = []
            for pe in prov_entries[:2]:
                src = pe.get("source_path", "")
                loc = pe.get("locator", {})
                span = loc.get("source_span")
                if span:
                    citation_lines.append(f"- {src} span={span}")
                else:
                    citation_lines.append(f"- {src}")

            citation_block = "\n".join(citation_lines) if citation_lines else "- (no provenance recorded)"

            doc = f"TITLE: {c.title}\nSUMMARY: {c.summary or ''}\nCITATIONS:\n{citation_block}".strip()

            results.append(
                SearchResult(
                    document=doc,
                    distance=max(0.0, 1.0 - score),
                    metadata={
                        "source": "compiled",
                        "concept_id": c.id,
                        "rank": rank,
                    },
                )
            )

        return results
