# IR Schema

This repository uses JSON Lines files to represent a compiled knowledge program.

## Files

- `concepts.jsonl` Concept nodes.
- `relations.jsonl` Directed edges between concepts.
- `provenance.jsonl` Evidence that binds concepts or relations to source spans.
- `manifest.json` Build metadata and file hashes.

## Stability

- IDs must remain stable across builds when the underlying meaning remains stable.
- Outputs must be deterministic given the same inputs and toolchain.

## Required fields

### Concept
- `id` stable concept ID
- `title` short label
- `summary` optional
- `tags` list

### Relation
- `id` stable relation ID
- `src` concept ID
- `dst` concept ID
- `type` prereq, depends_on, explains, contradicts, supports, example_of
- `weight` optional

### Provenance
- `id` stable provenance ID
- `target_id` concept or relation ID
- `source_path` relative path under `sources/`
- `source_sha256` sha256 of the raw source file
- `locator` span locator, for example `{page: 3, start: 120, end: 220}`
- `note` optional
