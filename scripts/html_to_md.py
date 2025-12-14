#!/usr/bin/env python3
"""Convert HTML to deterministic Markdown suitable for AXM sources.

This is a reference pipeline, not a universal ingestion tool.

Usage:
  python scripts/html_to_md.py input.html --out sources/my_pack/

Notes:
- Preserves headings, paragraphs, and lists
- Strips script/style and common navigation chrome
- Emits a provenance header block at the top of each file
"""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

from bs4 import BeautifulSoup
from markdownify import markdownify as md


def stable_slug(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "document"


def content_id(origin: str) -> str:
    h = hashlib.sha256(origin.encode("utf-8")).hexdigest()
    return h[:16]


def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # Remove common wiki/nav chrome by id/class hints
    drop_selectors = [
        ("div", {"id": "mw-navigation"}),
        ("div", {"id": "mw-head"}),
        ("div", {"id": "mw-panel"}),
        ("div", {"class": "navbox"}),
        ("table", {"class": "navbox"}),
        ("div", {"class": "toc"}),
        ("div", {"id": "toc"}),
        ("header", {}),
        ("footer", {}),
        ("nav", {}),
    ]
    for name, attrs in drop_selectors:
        for t in soup.find_all(name, attrs=attrs or None):
            t.decompose()

    body = soup.body or soup
    return str(body)


def to_markdown(html: str) -> str:
    text = md(html, heading_style="ATX")
    # Normalize whitespace deterministically
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="Path to HTML file")
    ap.add_argument("--out", required=True, help="Output directory under sources/")
    ap.add_argument("--source", default="HTML export", help="Provenance Source field")
    ap.add_argument("--license", default="UNKNOWN", help="Provenance License field")
    ap.add_argument("--retrieved-from", dest="retrieved_from", default=None, help="Provenance retrieved_from (URL/path)")
    ap.add_argument("--prepared-by", dest="prepared_by", default="scripts/html_to_md.py", help="Provenance prepared_by")
    ap.add_argument("--prepared-at", dest="prepared_at", default="2025-12-13", help="Provenance prepared_at (fixed for determinism)")
    ap.add_argument("--title", default=None, help="Override title")
    args = ap.parse_args()

    in_path = Path(args.input)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    html = in_path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")
    title = args.title or (soup.title.string.strip() if soup.title and soup.title.string else in_path.stem)

    cleaned = clean_html(html)
    md_text = to_markdown(cleaned)

    slug = stable_slug(title)
    out_path = out_dir / f"{slug}.md"

    origin = f"{args.source}:{in_path.name}"
    hdr = """---
title: "{title}"
origin: "{origin}"
origin_id: "{origin_id}"
license: "{license}"
retrieved_from: "{retrieved_from}"
prepared_by: "{prepared_by}"
prepared_at: "{prepared_at}"
---

""".format(
        title=title,
        origin=origin,
        origin_id=content_id(origin),
        license=args.license,
        retrieved_from=(args.retrieved_from or args.source),
        prepared_by=args.prepared_by,
        prepared_at=args.prepared_at,
    )out_path.write_text(hdr + "\n" + md_text, encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
