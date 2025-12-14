#!/usr/bin/env python3
"""
pack.py

Build and verify self-contained knowledge packs.

Design rules (v0.2):
- Packs are self-contained by default.
- Two pack flavors:
  * Audit pack: sources/ + compiled/ + manifest + checksums
  * Runtime pack: compiled/ + manifest + checksums (+ optional signatures)
- No external registry, cache, or network required to install, verify, or query.

This script intentionally stays small and boring.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import os
from pathlib import Path
from typing import Dict, List, Tuple

import yaml


REQUIRED_PROVENANCE_KEYS = [
    "title",
    "origin",
    "license",
]

DEFAULT_DIST_DIR = "dist"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def parse_provenance_block(md_text: str) -> Dict[str, str]:
    """
    Accepts either:
    1) YAML front matter:
       ---
       key: value
       ---
    2) Leading HTML comment block:
       <!--
       key: value
       -->
    """
    text = md_text.lstrip()

    # YAML front matter
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            block = text[3:end].strip()
            try:
                data = yaml.safe_load(block) or {}
                if isinstance(data, dict):
                    return {str(k): str(v) for k, v in data.items()}
            except Exception:
                pass

    # HTML comment front matter
    if text.startswith("<!--"):
        end = text.find("-->")
        if end == -1:
            return {}
        block = text[4:end].strip()
        out: Dict[str, str] = {}
        for line in block.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                continue
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
        return out

    return {}



def verify_sources_pack(pack_dir: Path) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    manifest_path = pack_dir / "manifest.yaml"
    if not manifest_path.exists():
        errors.append(f"Missing manifest.yaml at {manifest_path}")
        return False, errors

    manifest = load_manifest_yaml(manifest_path)
    files = manifest.get("files") or manifest.get("sources") or []
    if not isinstance(files, list) or not files:
        errors.append("manifest.yaml must contain a non-empty 'files' or 'sources' list")
        return False, errors

    for entry in files:
        rel = entry.get("path")
        expected = entry.get("sha256")
        if not rel or not expected:
            errors.append("Each manifest file entry must include 'path' and 'sha256'")
            continue
        fpath = pack_dir / rel
        # Allow manifest paths that include the repo-relative prefix "sources/<pack>/..."
        if not fpath.exists() and rel.startswith("sources/"):
            parts = rel.split("/", 2)
            if len(parts) >= 3:
                # parts[0] = "sources", parts[1] = "<pack_id>"
                fpath2 = pack_dir / parts[2]
                if fpath2.exists():
                    fpath = fpath2
        if not fpath.exists():
            errors.append(f"Missing source file: {rel}")
            continue
        actual = sha256_file(fpath)
        if actual != expected:
            errors.append(f"SHA256 mismatch for {rel}: expected {expected}, got {actual}")

        if fpath.suffix.lower() in (".md", ".txt"):
            if fpath.suffix.lower() == ".md":
                prov = parse_provenance_block(fpath.read_text(encoding="utf-8"))
                for k in REQUIRED_PROVENANCE_KEYS:
                    if k not in prov or not prov[k]:
                        errors.append(f"Missing provenance key '{k}' in {rel}")

    return len(errors) == 0, errors


def write_checksums(root: Path, files: List[Path], out_path: Path) -> None:
    lines: List[str] = []
    for f in sorted(files, key=lambda p: str(p)):
        rel = f.relative_to(root)
        lines.append(f"{sha256_file(f)}  {rel.as_posix()}")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def collect_files(base: Path) -> List[Path]:
    return [p for p in base.rglob("*") if p.is_file()]


def build_pack(repo_root: Path, pack_name: str, flavor: str, dist_dir: Path) -> Path:
    """
    Creates a self-contained zip file under dist_dir.
    """
    sources_dir = repo_root / "sources" / pack_name
    compiled_dir = repo_root / "compiled" / pack_name

    if not sources_dir.exists():
        raise SystemExit(f"Missing sources pack: {sources_dir}")
    if not compiled_dir.exists():
        raise SystemExit(f"Missing compiled pack: {compiled_dir}")

    ok, errors = verify_sources_pack(sources_dir)
    if not ok:
        raise SystemExit("Source pack verification failed:\n- " + "\n- ".join(errors))

    ensure_dir(dist_dir)

    pack_root = dist_dir / f"{pack_name}__{flavor}"
    if pack_root.exists():
        # clean
        for p in sorted(pack_root.rglob("*"), reverse=True):
            if p.is_file():
                p.unlink()
            else:
                p.rmdir()
        pack_root.rmdir()

    ensure_dir(pack_root)

    # Always include a pack manifest (json) that is stable and copy-friendly
    pack_manifest = {
        "pack_name": pack_name,
        "flavor": flavor,
        "layout_version": "v1",
        "self_contained": True,
    }
    (pack_root / "PACK_MANIFEST.json").write_text(
        json.dumps(pack_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    # Include content per flavor
    if flavor == "audit":
        # sources + compiled
        shutil_copytree(sources_dir, pack_root / "sources" / pack_name)
        shutil_copytree(compiled_dir, pack_root / "compiled" / pack_name)
    elif flavor == "runtime":
        shutil_copytree(compiled_dir, pack_root / "compiled" / pack_name)
        # optional signatures directory (empty placeholder)
        ensure_dir(pack_root / "signatures")
    else:
        raise SystemExit("Flavor must be 'audit' or 'runtime'")

    # checksums for everything inside the pack root (excluding the zip itself)
    all_files = collect_files(pack_root)
    write_checksums(pack_root, all_files, pack_root / "CHECKSUMS.sha256")

    # Write a short README
    readme = [
        f"# {pack_name} ({flavor} pack)",
        "",
        "This is a self-contained AXIOM knowledge pack.",
        "",
        "## Verify",
        "From inside this pack directory:",
        "",
        "```bash",
        "sha256sum -c CHECKSUMS.sha256",
        "```",
        "",
        "## Contents",
    ]
    if flavor == "audit":
        readme += [
            "- sources/ (human-auditable inputs)",
            "- compiled/ (deterministic compiled artifacts)",
        ]
    else:
        readme += [
            "- compiled/ (deterministic compiled artifacts)",
            "- signatures/ (optional; empty placeholder in v0.2)",
        ]
    (pack_root / "PACK_README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")

    # Zip it
    zip_path = dist_dir / f"{pack_name}__{flavor}.zip"
    zip_dir(pack_root, zip_path)

    return zip_path


def zip_dir(src_dir: Path, zip_path: Path) -> None:
    import zipfile
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(src_dir.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(src_dir).as_posix())


def shutil_copytree(src: Path, dst: Path) -> None:
    import shutil
    ensure_dir(dst.parent)
    shutil.copytree(src, dst)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("verify", help="Verify a sources/<pack> directory against its manifest and provenance contract")
    v.add_argument("--repo", default=".", help="Repo root")
    v.add_argument("--pack", required=True, help="Pack name (directory under sources/)")

    b = sub.add_parser("build", help="Build a self-contained pack zip (audit or runtime)")
    b.add_argument("--repo", default=".", help="Repo root")
    b.add_argument("--pack", required=True, help="Pack name (directory under sources/ and compiled/)")
    b.add_argument("--flavor", choices=["audit", "runtime"], required=True)
    b.add_argument("--out", default=DEFAULT_DIST_DIR, help="Output directory")

    args = ap.parse_args()
    repo_root = Path(args.repo).resolve()

    if args.cmd == "verify":
        ok, errors = verify_sources_pack(repo_root / "sources" / args.pack)
        if not ok:
            print("FAIL")
            for e in errors:
                print(f"- {e}")
            raise SystemExit(2)
        print("OK")
        return

    if args.cmd == "build":
        out_dir = (repo_root / args.out).resolve()
        zip_path = build_pack(repo_root, args.pack, args.flavor, out_dir)
        print(zip_path.as_posix())
        return


if __name__ == "__main__":
    main()
