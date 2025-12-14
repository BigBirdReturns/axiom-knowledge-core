from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from axiom_knowledge_core.ir.io import write_jsonl
from axiom_knowledge_core.ir.models import Concept, Provenance, Relation
from axiom_knowledge_core.utils.hashing import sha256_file


@dataclass(frozen=True)
class AxmCompileResult:
    concepts: list[Concept]
    relations: list[Relation]
    provenance: list[Provenance]


def find_axm_available() -> bool:
    """Return True if the Python package `axm` is importable."""
    try:
        import axm  # noqa: F401

        return True
    except Exception:
        return False


def _relation_type(predicate: str) -> str:
    p = (predicate or "").lower()
    if p in {"prereq", "prerequisite", "requires"}:
        return "prereq"
    if p in {"depends_on", "depends", "dependency"}:
        return "depends_on"
    if p in {"supports", "support"}:
        return "supports"
    if p in {"contradicts", "contradict"}:
        return "contradicts"
    if p in {"example_of", "example"}:
        return "example_of"
    return "explains"


def _stable_rel_id(src: str, typ: str, dst: str) -> str:
    h = hashlib.sha256(f"{src}|{typ}|{dst}".encode("utf-8")).hexdigest()
    return f"rel:{h[:16]}"


def compile_sources_to_ir(*, sources_dir: Path, out_dir: Path) -> AxmCompileResult:
    """Compile sources using AXM (Python API) and materialize AXIOM IR JSONL.

    This adapter treats AXM programs as an extraction backend and converts AXM nodes
    and relations into the smaller AXIOM IR contract.
    """

    from axm.compiler import Config, compile as axm_compile

    concepts: list[Concept] = []
    relations: list[Relation] = []
    provenance: list[Provenance] = []

    # For de-dup within this compile.
    seen_concepts: set[str] = set()
    seen_prov: set[str] = set()
    seen_rels: set[str] = set()

    # Compile each source file into an AXM Program, then translate.
    for p in sorted(sources_dir.rglob("*")):
        if not p.is_file() or p.name.startswith("."):
            continue

        file_sha = sha256_file(p)
        rel_path = str(p.relative_to(sources_dir))

        # Deterministic, offline-friendly path.
        cfg = Config.no_llm()
        program = axm_compile(str(p), cfg)

        # Translate nodes to concepts.
        for node_id, node in program.nodes.items():
            if node_id not in seen_concepts:
                concepts.append(
                    Concept(
                        id=node_id,
                        title=node.label,
                        summary=str(node.value) if node.value is not None else None,
                        tags=[str(node.coord.major)],
                    )
                )
                seen_concepts.add(node_id)

            prov = program.provenance.get(node.prov_id)
            if prov:
                prov_id = f"prov:{prov.prov_id}"
                if prov_id not in seen_prov:
                    locator: dict[str, Any] = {
                        "chunk_id": prov.chunk_id,
                        "tier": prov.tier,
                        "confidence": prov.confidence,
                    }
                    if prov.source_start is not None:
                        locator["source_span"] = {"start": prov.source_start, "end": prov.source_end}

                    provenance.append(
                        Provenance(
                            id=prov_id,
                            target_id=node_id,
                            source_path=rel_path,
                            source_sha256=file_sha,
                            locator=locator,
                            note=f"extractor={prov.extractor}",
                        )
                    )
                    seen_prov.add(prov_id)

        # Translate relations.
        for rel in program.relations:
            typ = _relation_type(rel.predicate)
            rid = _stable_rel_id(rel.subject_id, typ, rel.object_id)
            if rid in seen_rels:
                continue
            relations.append(
                Relation(
                    id=rid,
                    src=rel.subject_id,
                    dst=rel.object_id,
                    type=typ,  # type: ignore[arg-type]
                    weight=float(rel.confidence or 1.0),
                )
            )
            seen_rels.add(rid)

            # Attach provenance for relation, mapped to its prov.
            prov = program.provenance.get(rel.prov_id)
            if prov:
                prov_id = f"prov:{prov.prov_id}:{rid}"
                if prov_id not in seen_prov:
                    locator: dict[str, Any] = {
                        "chunk_id": prov.chunk_id,
                        "tier": prov.tier,
                        "confidence": prov.confidence,
                    }
                    if prov.source_start is not None:
                        locator["source_span"] = {"start": prov.source_start, "end": prov.source_end}
                    provenance.append(
                        Provenance(
                            id=prov_id,
                            target_id=rid,
                            source_path=rel_path,
                            source_sha256=file_sha,
                            locator=locator,
                            note=f"extractor={prov.extractor}",
                        )
                    )
                    seen_prov.add(prov_id)

    out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(out_dir / "concepts.jsonl", [c.model_dump() for c in concepts])
    write_jsonl(out_dir / "relations.jsonl", [r.model_dump() for r in relations])
    write_jsonl(out_dir / "provenance.jsonl", [p.model_dump() for p in provenance])

    return AxmCompileResult(concepts=concepts, relations=relations, provenance=provenance)


def find_axm_bin(explicit: Optional[str] = None) -> Optional[str]:
    """Backward-compatible shim.

    The monorepo uses the AXM Python API, so this returns a sentinel when AXM is importable.
    """

    _ = explicit
    return "python:axm" if find_axm_available() else None


def run_axm_compile(*, sources_dir: Path, out_dir: Path, axm_bin: str) -> None:
    """Adapter entrypoint used by compiler.py.

    In this repo, `axm_bin` is a sentinel string and compilation happens via Python import.
    """

    _ = axm_bin
    compile_sources_to_ir(sources_dir=sources_dir, out_dir=out_dir)
