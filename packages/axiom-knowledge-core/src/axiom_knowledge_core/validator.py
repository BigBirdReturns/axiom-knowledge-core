from __future__ import annotations

from pathlib import Path

import orjson

from axiom_knowledge_core.ir.io import read_jsonl
from axiom_knowledge_core.utils.hashing import sha256_file


class ValidationError(RuntimeError):
    pass


def validate_compiled_dir(compiled_dir: Path) -> None:
    required = [
        compiled_dir / "concepts.jsonl",
        compiled_dir / "relations.jsonl",
        compiled_dir / "provenance.jsonl",
        compiled_dir / "manifest.json",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise ValidationError("Missing required compiled files: " + ", ".join(missing))

    # Parse JSONL
    concepts = read_jsonl(compiled_dir / "concepts.jsonl")
    relations = read_jsonl(compiled_dir / "relations.jsonl")
    provenance = read_jsonl(compiled_dir / "provenance.jsonl")

    # Unique IDs
    def require_unique(records: list[dict], label: str) -> None:
        ids = [r.get("id") for r in records]
        if any(i is None for i in ids):
            raise ValidationError(f"{label} contains records without id")
        dup = {i for i in ids if ids.count(i) > 1}
        if dup:
            raise ValidationError(f"{label} contains duplicate ids: {sorted(list(dup))[:10]}")

    require_unique(concepts, "concepts")
    require_unique(relations, "relations")
    require_unique(provenance, "provenance")

    # Provenance target exists
    concept_ids = {c["id"] for c in concepts}
    relation_ids = {r["id"] for r in relations}
    for p in provenance:
        tid = p.get("target_id")
        if tid not in concept_ids and tid not in relation_ids:
            raise ValidationError(f"provenance target_id not found in concepts or relations: {tid}")

    # Manifest hash check
    manifest_path = compiled_dir / "manifest.json"
    manifest = orjson.loads(manifest_path.read_bytes())
    outputs = manifest.get("outputs_sha256", {})
    for fname, expected in outputs.items():
        fpath = compiled_dir / fname
        if not fpath.exists():
            raise ValidationError(f"manifest references missing output: {fname}")
        actual = sha256_file(fpath)
        if actual != expected:
            raise ValidationError(f"hash mismatch for {fname}: expected {expected}, got {actual}")


# Backwards-compatible alias.
def validate_compiled(compiled_dir: str | Path) -> list[str]:
    """Validate a compiled directory and return a list of errors.

    This function is intentionally non-throwing to support CI/reporting.
    """
    try:
        validate_compiled_dir(Path(compiled_dir))
        return []
    except Exception as e:
        return [str(e)]
