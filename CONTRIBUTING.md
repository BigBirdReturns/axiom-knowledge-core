# Contributing

This repository is correctness-first.

It treats knowledge as a compiled program:

1. Contributors submit sources.
2. The system compiles deterministic artifacts.
3. Tutors, dashboards, curricula, and QA render views over compiled artifacts.

Runtime components must not read raw sources.

## Preparing sources for compilation

This repository is a knowledge compiler. It is not a scraping archive.

Contributors submit compiler-ready sources. The compiler produces the authoritative artifacts.

### Accepted inputs in `sources/`

Only these file types are accepted under `sources/`:

- Markdown: `.md` (preferred)
- Plain text: `.txt`

Any other type under `sources/` will be rejected by CI.

### Disallowed inputs in `sources/`

Do not submit these formats under `sources/`:

- PDF, HTML, ZIM, EPUB, DOCX, PPTX
- Images, audio, video
- Archives (`.zip`, `.tar.gz`)

If your upstream source is one of these formats, convert it to `.md` or `.txt` first.

### Required provenance header

Every source file must begin with a provenance header.

For Markdown:

```markdown
---
title: "<human readable title>"
origin: "<where it came from, for example RFC 2119, OpenStax Biology 2e, Kiwix ZIM: wikipedia_en_all_maxi_2024-xx>"
origin_id: "<stable ID, for example rfc:2119, openstax:biology2e:ch1, zim:wikipedia:Thermodynamics>"
license: "<license string, for example IETF Trust, CC BY-SA 4.0, CC BY 4.0>"
retrieved_from: "<url or zim entry path or isbn>"
prepared_by: "<your handle>"
prepared_at: "<YYYY-MM-DD>"
prep_tool: "<optional, for example scripts/html_to_md.py@<git sha>>"
notes: "<optional>"
---
```

For plain text:

```text
TITLE: <human readable title>
ORIGIN: <where it came from>
ORIGIN_ID: <stable ID>
LICENSE: <license string>
RETRIEVED_FROM: <url or zim entry path>
PREPARED_BY: <your handle>
PREPARED_AT: <YYYY-MM-DD>
PREP_TOOL: <optional>
NOTES: <optional>

<blank line, then content begins>
```

CI will reject sources missing a provenance header.

### Conversion requirements

Converted sources must meet these requirements:

- Preserve semantic structure: headings, lists, numbered clauses.
- Remove navigation and layout noise: menus, footers, sidebars, link farms.
- Keep citations if present, but do not inline large reference lists if they are boilerplate.
- Deterministic output: the same upstream input must produce identical `.md` or `.txt`.

Do not include nondeterministic markers such as:

- timestamps inside the content body
- generated-at banners
- randomized ordering

### File naming and layout

Use stable, predictable paths:

- `sources/<pack>/<domain>/<slug>.md`
- `sources/<pack>/<domain>/<slug>.txt`

Examples:

- `sources/rfc-mini/web/rfc_2119.md`
- `sources/wiki/physics/thermodynamics.md`

Avoid spaces in filenames.

## Submitting a knowledge pack

A pack is a collection of sources prepared for compilation.

Minimum pack requirements:

- One or more `.md` or `.txt` files under `sources/<pack>/...`
- Every file contains the required provenance header
- Licenses are compatible with redistribution

Recommended:

- `sources/<pack>/manifest.yaml` describing the pack

Suggested manifest format:

```yaml
pack:
  name: "<pack name>"
  version: "0.1.0"
  description: "<one sentence>"
  maintainer: "<handle>"
  license_policy: "<notes>"
sources:
  - path: "sources/<pack>/<domain>/<file>.md"
    origin_id: "<origin_id>"
    license: "<license>"
    title: "<title>"
```

## Local build

Run these from repo root:

```bash
ak compile --sources sources --out compiled
ak derive --compiled compiled
ak validate --compiled compiled
```

Optional determinism check:

```bash
rm -rf compiled_rebuild
ak compile --sources sources --out compiled_rebuild
ak derive --compiled compiled_rebuild
python scripts/ci_compare_compiled.py compiled compiled_rebuild
```

## What reviewers check

Reviewers accept PRs based on:

- provenance completeness
- deterministic and readable diffs
- compile, derive, validate succeed
- minimal and expected diffs in compiled artifacts

This repository treats compiled artifacts as a build output. If sources are not compiler-grade, the PR is rejected.
---

## Reference preparation pipelines (optional)

This repository may include small, pinned, deterministic reference pipelines under `scripts/` and `docs/recipes/`.

These are not part of the compiler. They exist to help contributors converge on consistent `.md` outputs.

- `scripts/html_to_md.py` converts a single HTML file into canonical Markdown with required provenance front matter.
- `docs/recipes/kiwix_zim_to_sources.md` describes a reproducible Kiwix workflow that extracts ZIM content upstream and converts it into `sources/` inputs.
