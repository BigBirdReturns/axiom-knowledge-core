# Kiwix and ZIM ingestion recipe

This repo does not accept ZIM files in `sources/`. Treat ZIM as an upstream container and convert pages into Markdown or plain text before running the compiler.

This document describes two reproducible approaches.

## Approach A: Use zim-tools (zimdump)

1. Install zim-tools from openZIM (package name may vary by OS).

2. Inspect the archive:

```
zimdump info path/to/corpus.zim
```

3. List entries and pick a subset (examples vary by corpus):

```
zimdump list path/to/corpus.zim > entries.txt
```

4. Dump a single entry to HTML:

```
zimdump dump --redirect path/to/corpus.zim A/Some_Page > page.html
```

5. Convert HTML to Markdown using the repo reference script:

```
pip install -r scripts/requirements-prep.txt
python scripts/html_to_md.py page.html --out sources/kiwix_seed --source "Kiwix ZIM" --license "CC BY-SA 4.0"
```

6. Compile:

```
python -m axiom_knowledge_core.cli compile --sources sources/kiwix_seed --out compiled/kiwix_seed
```

Notes:
- Use stable entry paths as the origin field.
- Keep conversion deterministic by pinning your tool versions.

## Approach B: Use python-libzim for programmatic extraction

If you want automation, use the `libzim` Python binding and write an extractor that:
- reads entries by path
- resolves redirects to canonical entries
- writes one `.md` file per entry under `sources/<pack>/`

See the libzim docs for the Archive and Entry interfaces.

## Provenance expectations

Every generated `.md` file must include a provenance header at the top, for example:

```md
<!--
Source: Wikipedia (Kiwix ZIM)
Article: Thermodynamics
Origin: A/Thermodynamics
License: CC BY-SA 4.0
-->
```

Do not include timestamps inside the content body. If you store retrieval time, store it only in the provenance header and exclude it from any content hashing you use for stable IDs.
