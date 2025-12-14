from __future__ import annotations

import hashlib
from pathlib import Path
import sys

REQUIRED_FILES = [
    "concepts.jsonl",
    "relations.jsonl",
    "provenance.jsonl",
    "manifest.json",
]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fail(msg: str) -> None:
    sys.stderr.write(msg + "\n")
    raise SystemExit(2)


def main() -> None:
    if len(sys.argv) != 3:
        fail("Usage: python scripts/ci_compare_compiled.py <dir_a> <dir_b>")

    a = Path(sys.argv[1])
    b = Path(sys.argv[2])

    for fname in REQUIRED_FILES:
        pa = a / fname
        pb = b / fname
        if not pa.exists():
            fail(f"Missing required compiled file in {a}: {fname}")
        if not pb.exists():
            fail(f"Missing required compiled file in {b}: {fname}")

        ha = sha256_file(pa)
        hb = sha256_file(pb)
        if ha != hb:
            fail(f"Determinism failure: {fname} differs.\n{a}: {ha}\n{b}: {hb}")

    sys.stdout.write("compiled determinism: OK\n")


if __name__ == "__main__":
    main()
