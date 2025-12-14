from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from axiom_knowledge_core.axm.adapter import find_axm_bin, run_axm_compile
from axiom_knowledge_core.ir.io import write_jsonl
from axiom_knowledge_core.ir.models import Concept, Manifest, Provenance
from axiom_knowledge_core.utils.hashing import sha256_file


@dataclass(frozen=True)
class CompileOptions:
    sources_dir: Path
    out_dir: Path
    axm_bin: str | None = None
    tool_name: str = "axiom-knowledge-core"
    tool_version: str = "0.1.0"



def _ensure_compiled_outputs(sources_dir: Path, out_dir: Path, tool: str, tool_version: str) -> None:
    """Ensure required compiled files exist and write a manifest if missing."""
    out_dir.mkdir(parents=True, exist_ok=True)
    concepts_path = out_dir / "concepts.jsonl"
    relations_path = out_dir / "relations.jsonl"
    provenance_path = out_dir / "provenance.jsonl"
    manifest_path = out_dir / "manifest.json"

    # Create missing required files (empty) if the delegated compiler did not emit them.
    if not concepts_path.exists():
        concepts_path.write_text("", encoding="utf-8")
    if not relations_path.exists():
        relations_path.write_text("", encoding="utf-8")
    if not provenance_path.exists():
        provenance_path.write_text("", encoding="utf-8")

    if manifest_path.exists():
        return

    sources_sha = {
        str(p.relative_to(sources_dir)): sha256_file(p)
        for p in sorted(sources_dir.rglob("*"))
        if p.is_file() and not p.name.startswith(".")
    }
    outputs_sha = {
        "concepts.jsonl": sha256_file(concepts_path),
        "relations.jsonl": sha256_file(relations_path),
        "provenance.jsonl": sha256_file(provenance_path),
    }
    manifest = Manifest(
        built_at_utc=datetime.now(timezone.utc).isoformat(),
        tool=tool,
        tool_version=tool_version,
        sources_sha256=sources_sha,
        outputs_sha256=outputs_sha,
        counts={
            "concepts": sum(1 for _ in concepts_path.open("r", encoding="utf-8") if _.strip()),
            "relations": sum(1 for _ in relations_path.open("r", encoding="utf-8") if _.strip()),
            "provenance": sum(1 for _ in provenance_path.open("r", encoding="utf-8") if _.strip()),
        },
    )
    manifest_path.write_bytes(
        __import__("orjson").dumps(manifest.model_dump(), option=__import__("orjson").OPT_SORT_KEYS)
    )


def compile_knowledge(opts: CompileOptions) -> Path:
    """Compile sources into compiled artifacts.

    If an AXM binary is available, this function will delegate to AXM.
    Otherwise, it will produce a minimal IR for demonstration and tests.
    """
    sources_dir = opts.sources_dir
    out_dir = opts.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    axm_bin = find_axm_bin(opts.axm_bin)
    if axm_bin:
        run_axm_compile(sources_dir=sources_dir, out_dir=out_dir, axm_bin=axm_bin)
        _ensure_compiled_outputs(sources_dir, out_dir, opts.tool_name, opts.tool_version)
        return out_dir

    # Built-in minimal compiler
    concepts: list[Concept] = []
    prov: list[Provenance] = []

    for p in sorted(sources_dir.rglob("*")):
        if not p.is_file():
            continue
        if p.name.startswith("."):
            continue

        file_sha = sha256_file(p)
        cid = f"concept:source:{file_sha[:16]}"
        concepts.append(
            Concept(
                id=cid,
                title=p.stem,
                summary="Source placeholder concept produced by the built-in compiler.",
                tags=[p.suffix.lstrip(".") or "file"],
            )
        )
        prov.append(
            Provenance(
                id=f"prov:{file_sha[:16]}",
                target_id=cid,
                source_path=str(p.relative_to(sources_dir)),
                source_sha256=file_sha,
                locator={},
                note="Built-in compiler does not extract spans.",
            )
        )

    concepts_path = out_dir / "concepts.jsonl"
    relations_path = out_dir / "relations.jsonl"
    provenance_path = out_dir / "provenance.jsonl"

    write_jsonl(concepts_path, [c.model_dump() for c in concepts])
    write_jsonl(relations_path, [])
    write_jsonl(provenance_path, [p.model_dump() for p in prov])

    sources_sha = {
        str(p.relative_to(sources_dir)): sha256_file(p)
        for p in sorted(sources_dir.rglob("*"))
        if p.is_file() and not p.name.startswith(".")
    }
    outputs_sha = {
        "concepts.jsonl": sha256_file(concepts_path),
        "relations.jsonl": sha256_file(relations_path),
        "provenance.jsonl": sha256_file(provenance_path),
    }
    manifest = Manifest(
        built_at_utc=datetime.now(timezone.utc).isoformat(),
        tool=opts.tool_name,
        tool_version=opts.tool_version,
        sources_sha256=sources_sha,
        outputs_sha256=outputs_sha,
        counts={
            "concepts": len(concepts),
            "relations": 0,
            "provenance": len(prov),
        },
    )

    (out_dir / "manifest.json").write_bytes(
        __import__("orjson").dumps(manifest.model_dump(), option=__import__("orjson").OPT_SORT_KEYS)
    )

    return out_dir


# Backwards-compatible alias used by tests and earlier docs.
def compile_sources(sources_dir: str | Path, out_dir: str | Path) -> Path:
    """Compile sources into AXIOM artifacts.

    Backwards-compatible helper for tests and scripts.
    """
    opts = CompileOptions(sources_dir=Path(sources_dir), out_dir=Path(out_dir))
    return compile_knowledge(opts)
