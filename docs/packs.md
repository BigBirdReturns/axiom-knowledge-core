# Knowledge Packs

A knowledge pack is a self-contained unit of knowledge input and output.

A pack exists so anyone can:

- review sources in a pull request
- rebuild deterministically
- verify integrity offline
- copy and run on an air-gapped device

## Core rule for v0.2

A pack must be installable, verifiable, and queryable with no external dependencies.

No registry.
No shared shard store.
No required cache.

## Pack flavors

v0.2 defines two flavors. Both are self-contained.

### 1) Audit Pack

Use for PRs, review, and rebuild proofs.

Includes:

- `sources/<pack>/` (human-auditable inputs)
- `compiled/<pack>/` (deterministic compiled artifacts)
- `PACK_MANIFEST.json`
- `CHECKSUMS.sha256`

### 2) Runtime Pack

Use for devices, distribution, and offline deployment.

Includes:

- `compiled/<pack>/`
- `PACK_MANIFEST.json`
- `CHECKSUMS.sha256`
- optional `signatures/` (empty placeholder in v0.2)

## Source pack contract

Submit packs under:

`source/<pack_id>/`

Each pack must include:

- `manifest.yaml` with `files[].path` and `files[].sha256`
- only `.md` and `.txt` files
- provenance header in every `.md` file

Provenance header format:

```md
<!--
title: ...
origin: ...
license: ...
-->
```

This repository treats source preparation as contributor responsibility.
The compiler is not a scraper.

## Build and verify packs

This repo includes a small pack tool:

```bash
python scripts/pack.py verify --pack <pack_id>
python scripts/pack.py build --pack <pack_id> --flavor audit
python scripts/pack.py build --pack <pack_id> --flavor runtime
```

Output zips land in `dist/` by default.

## Granularity rule

Use one pack per source collection, not per chapter.

Examples:

- `first-aid-fm21-11`
- `openstax-biology-2e`
- `rfc-mini`

You can create chapter views inside the compiled artifacts.
Do not explode the repository into thousands of tiny packs.
