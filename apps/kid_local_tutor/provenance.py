"""provenance.py

Strict runtime provenance contract enforcement for the tutor.

Goal: make it impossible for the tutor to emit uncited factual claims when
running in compiled-substrate mode (or any mode).
"""

from __future__ import annotations

import re
from typing import List, Tuple, Any

_CITATION_SENT_RE = re.compile(r"\[(\d+)\]")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[\.!\?])\s+")


def _is_allowed_uncited(sentence: str) -> bool:
    s = sentence.strip().lower()
    if not s:
        return True
    allowed_prefixes = [
        "i do not know from this local library",
        "i cannot find that in the local library",
        "i cannot answer from this local library",
        "please ask a more specific question",
    ]
    return any(s.startswith(p) for p in allowed_prefixes)


def _looks_like_claim(sentence: str) -> bool:
    s = sentence.strip()
    if not s:
        return False
    if s.endswith("?"):
        return False
    # If the sentence already includes citations, treat it as a claim that must validate.
    if _CITATION_SENT_RE.search(s):
        return True
    claim_markers = [
        " is ",
        " are ",
        " means ",
        " causes ",
        " should ",
        " must ",
        " always ",
        " never ",
    ]
    s_l = f" {s.lower()} "
    return any(m in s_l for m in claim_markers) or s.endswith(".")


def validate_provenance_contract(text: str, results: List[Any]) -> Tuple[bool, str]:
    """Validate that every claim sentence includes citations that resolve to retrieved context items."""
    valid_ids = set(range(1, len(results) + 1))

    raw_sentences = [s.strip() for s in _SENTENCE_SPLIT_RE.split(text.strip()) if s.strip()]

    # Normalize split artifacts so patterns like "Claim. [1]" remain attached to the claim.
    sentences: List[str] = []
    for s in raw_sentences:
        # If a fragment starts with citations, attach those citations to the previous sentence.
        if sentences:
            m = re.match(r"^(\[(?:\d+)\](?:\s*\[(?:\d+)\])*)\s+(.*)$", s)
            if m and m.group(1):
                sentences[-1] = sentences[-1].rstrip() + " " + m.group(1).strip()
                s = m.group(2).strip()
                if not s:
                    continue

        # Merge citation-only fragments like "[2]" into the previous sentence.
        if re.fullmatch(r"\[(\d+)\](\s*\[(\d+)\])*", s) and sentences:
            sentences[-1] = sentences[-1].rstrip() + " " + s
            continue

        sentences.append(s)

    bad = []

    for s in sentences:
        if _is_allowed_uncited(s):
            continue
        if not _looks_like_claim(s):
            continue
        cites = [int(x) for x in _CITATION_SENT_RE.findall(s)]
        if not cites:
            bad.append(f"Missing citation: {s}")
            continue
        for c in cites:
            if c not in valid_ids:
                bad.append(f"Invalid citation [{c}] in: {s}")

    if bad:
        return False, "\n".join(bad)
    return True, ""




def _build_sources_block(results: List[Any], used_ids: List[int]) -> str:
    lines = ["", "Sources:"]
    for cid in used_ids:
        idx = cid - 1
        if idx < 0 or idx >= len(results):
            continue
        r = results[idx]
        doc = getattr(r, "document", None)
        if doc is None and isinstance(r, dict):
            doc = r.get("document", "")
        doc = (doc or "").strip()

        prov_lines = []
        in_citations = False
        for ln in doc.splitlines():
            if ln.strip().upper().startswith("CITATIONS:"):
                in_citations = True
                continue
            if in_citations and ln.strip():
                prov_lines.append(ln.strip())
        if not prov_lines:
            prov_lines = ["(no provenance lines found in context item)"]

        lines.append(f"[{cid}] " + " | ".join(prov_lines[:3]))
    return "\n".join(lines)


def enforce_provenance_contract(text: str, results: List[Any]) -> str:
    ok, report = validate_provenance_contract(text, results)
    if not ok:
        top = min(3, len(results))
        preview = []
        for i in range(top):
            r = results[i]
            doc = getattr(r, "document", None)
            if doc is None and isinstance(r, dict):
                doc = r.get("document", "")
            doc = (doc or "").strip()
            if "CITATIONS:" in doc:
                preview.append(f"[{i+1}] " + doc.split("CITATIONS:", 1)[-1].strip().replace("\n", " "))
            else:
                preview.append(f"[{i+1}] " + " ".join(doc.split()[:40]))

        return (
            "I cannot answer from this local library without sources. "
            "Please ask a narrower question that matches the local materials.\n\n"
            "Top local sources:\n" + "\n".join(preview)
        )

    if "Sources:" not in text:
        used = sorted({int(x) for x in _CITATION_SENT_RE.findall(text)})
        return text.rstrip() + _build_sources_block(results, used)
    return text
