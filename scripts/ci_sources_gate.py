from __future__ import annotations

import re
from pathlib import Path
import sys

ALLOWED_EXTS = {".md", ".txt", ".yaml", ".yml"}

MD_REQUIRED_KEYS = {
    "title:",
    "origin:",
    "origin_id:",
    "license:",
    "retrieved_from:",
    "prepared_by:",
    "prepared_at:",
}
TXT_REQUIRED_KEYS = {
    "TITLE:",
    "ORIGIN:",
    "ORIGIN_ID:",
    "LICENSE:",
    "RETRIEVED_FROM:",
    "PREPARED_BY:",
    "PREPARED_AT:",
}


def fail(msg: str) -> None:
    sys.stderr.write(msg + "\n")
    raise SystemExit(2)


def check_allowed_files() -> None:
    sources = Path("sources")
    if not sources.exists():
        fail("sources/ directory is missing.")

    for p in sources.rglob("*"):
        if p.is_dir():
            continue
        ext = p.suffix.lower()
        if ext not in ALLOWED_EXTS:
            fail(f"Disallowed file type under sources/: {p} (allowed: .md, .txt, manifest.yaml)")
        if ext in {".yaml", ".yml"} and p.name not in {"manifest.yaml", "manifest.yml"}:
            fail(f"Only manifest.yaml is allowed under sources/ for YAML files: {p}")


def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="strict")


def check_md_header(text: str, p: Path) -> None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        fail(f"Missing provenance front matter in {p}. Expected '---' on first line.")

    end_idx = None
    for i in range(1, min(len(lines), 200)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        fail(f"Unclosed provenance front matter in {p}. Missing closing '---'.")

    header = "\n".join(lines[: end_idx + 1]).lower()
    missing = [k for k in sorted(MD_REQUIRED_KEYS) if k not in header]
    if missing:
        fail(f"Missing required provenance keys in {p}: {', '.join(missing)}")


def check_txt_header(text: str, p: Path) -> None:
    head = "\n".join(text.splitlines()[:30]).upper()
    missing = [k for k in sorted(TXT_REQUIRED_KEYS) if k not in head]
    if missing:
        fail(f"Missing required provenance keys in {p}: {', '.join(missing)}")


def check_provenance_headers() -> None:
    sources = Path("sources")
    for p in sources.rglob("*"):
        if p.is_dir():
            continue
        text = read_text(p)
        if p.suffix.lower() == ".md":
            check_md_header(text, p)
        elif p.suffix.lower() == ".txt":
            check_txt_header(text, p)


def main() -> None:
    check_allowed_files()
    check_provenance_headers()
    sys.stdout.write("sources gate: OK\n")


if __name__ == "__main__":
    main()
