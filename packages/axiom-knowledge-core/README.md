# AXIOM Knowledge Core

AXIOM Knowledge Core compiles raw sources into deterministic knowledge artifacts that can power offline tutors, curricula, and dashboards without requiring runtime meaning decisions.

The core rule:

- Compile meaning once.
- Render many times.

## What this repository includes

- A compiled IR format (JSONL) with stable IDs, provenance, and confidence.
- A local validator, packager, and diff-friendly manifest.
- A starter offline tutor codebase (ported in) that can be wired to the compiled IR.

## What this repository is not

- Not an LMS.
- Not a portal.
- Not a content farm.
- Not a chat-with-PDF wrapper.

## Repository layout

- `sources/` input materials (PDF, Markdown, HTML dumps, text)
- `compiled/` compiled artifacts (authoritative output)
- `views/` renderers (tutor, curriculum, dashboard)
- `src/axiom_knowledge_core/` Python package

## Compiled IR contract

The compiled output is a set of JSONL files:

- `compiled/concepts.jsonl` concept nodes
- `compiled/relations.jsonl` directed edges (prereq, depends_on, explains, contradicts)
- `compiled/provenance.jsonl` span-accurate citations for claims and nodes
- `compiled/manifest.json` hashes, counts, and build metadata

Every factual statement must map to provenance.

## Quick start

1) Create a virtual environment and install dependencies.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

2) Add sources.

```bash
cp path/to/document.pdf sources/
```

3) Compile.

```bash
ak compile --sources sources --out compiled
```

4) Validate.

```bash
ak validate --compiled compiled
```

5) Run a text QA view over compiled artifacts.

```bash
ak qa --compiled compiled --question "What are the prerequisites for CPR?"
```

## Using AXM

This repo includes an adapter that can call an external AXM compiler if it is installed.

- If AXM is present, `ak compile` will attempt to invoke it.
- If AXM is not present, `ak compile` can still produce a minimal IR using the built-in toy compiler (useful for tests and first demos).

## Offline tutor

The `src/axiom_knowledge_core/tutor/kid_local_tutor` package is included as a working offline tutor foundation.

This repo does not require the tutor to trust the model for facts.

The intended integration is:

- Retrieval pulls a subgraph from `compiled/`.
- The tutor renders from that subgraph.
- Any LLM usage is limited to phrasing and pedagogy, never factual invention.

## License

See `LICENSE`.
