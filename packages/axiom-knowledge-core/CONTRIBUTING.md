# Contributing

This repository treats a body of knowledge as a compiled artifact.

## What to submit

Submit one of the following:

1) Sources
- Add new primary sources under `sources/`.
- Prefer open licenses or public domain.
- Keep filenames stable.

2) Structural patches
- Add or edit IR records under `views/patches/` (planned) or submit a minimal JSONL patch file.
- Propose new concepts and relations with explicit provenance references.

3) Tests
- Add regression tests under `tests/` that encode expected prerequisite chains or expected cited answers.

## Rules

- Every factual claim must map to provenance.
- Prefer deterministic outputs and stable IDs.
- Keep changes small and diffable.

## Review checklist

- Sources are verifiable and properly referenced.
- New nodes and relations include provenance.
- `ak validate` passes.
