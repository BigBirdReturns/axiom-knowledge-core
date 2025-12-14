# Spectra Knowledge Stack

This repo stitches together three concrete building blocks into one offline-first pipeline:

1) **AXM** (semantic compiler)
2) **AXIOM Knowledge Core** (compiled knowledge repo shape, IR, validation, CI boundary)
3) **Kid Local Tutor** (offline tutor runtime, now able to pull context from compiled artifacts)

The goal is simple:

- People submit sources.
- The system compiles them into deterministic, diffable artifacts.
- Tutors, dashboards, curricula, and QA become views over that compiled substrate.

## Repo layout

- `packages/axm/`
  - AXM v0.5.3 (as provided)
- `packages/axiom-knowledge-core/`
  - Knowledge GitHub seed repo (as provided)
  - Updated AXM adapter that compiles via the AXM Python API and writes AXIOM IR
- `apps/kid_local_tutor/`
  - Offline tutor runtime (as provided)
  - Added `CompiledStore` so the tutor can read AXIOM compiled artifacts
- `docs/reference/`
  - Reference PDF: Indicators Dashboard + Offline QA Tutor

## Quickstart

### 1) Create a virtualenv and install the packages

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e packages/axm
pip install -e packages/axiom-knowledge-core
pip install -r apps/kid_local_tutor/requirements.txt
```

### 2) Compile sources into deterministic artifacts

Put sources under:

- `sources/` (or any folder you pass to the CLI)

Run:

```bash
ak compile --sources sources --out compiled
```

Outputs:

- `compiled/concepts.jsonl`
- `compiled/relations.jsonl`
- `compiled/provenance.jsonl`
- `compiled/manifest.json`

### 3) Run the tutor using compiled artifacts

The Streamlit app can use compiled artifacts as its retrieval backend.

```bash
export TUTOR_COMPILED_DIR=compiled
streamlit run apps/kid_local_tutor/app.py
```

If `TUTOR_COMPILED_DIR` is not set but `./compiled/` exists, the tutor uses it automatically.

Vector store mode is disabled by default. Enable it only when you explicitly want the legacy RAG path:

```bash
export TUTOR_VECTOR_MODE=1
```

## Design rules

- Compiled artifacts are the source of truth.
- Runtime systems are renderers.
- Factual sentences should have provenance anchors. If the local library does not cover a question, the tutor should say so.

## Adding knowledge

This repo only compiles sources that are already in a canonical, reviewable form.

- Only submit `.md`, `.txt`, and `.rst` (with preserved structure) under `sources/`
- Every source file should start with a provenance header block
- Do not commit PDFs, HTML, or ZIM files under `sources/`

See `CONTRIBUTING.md` for the full contract.

For reference conversion pipelines (HTML to Markdown, Kiwix notes), see `scripts/` and `docs/recipes/`.

## Next build steps

- Add a first-class tutor view contract in `axiom-knowledge-core/views/tutor/`.
- Add a compiled-subgraph query API (graph expansion plus deterministic ranking).
- Enforce a strict citation contract in the tutor (no provenance, no factual sentence).
- Package “corpus packs” for offline distribution (USB, SD card, local mesh).


## Correctness-first tutor defaults

- The tutor prefers compiled artifacts.
- Vector retrieval is disabled unless you set `TUTOR_VECTOR_MODE=1`.

Example:

```bash
make compile
TUTOR_COMPILED_DIR=compiled streamlit run apps/kid_local_tutor/app.py
```
