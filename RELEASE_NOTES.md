# Release Notes

## v0.2.0

This release locks the repository identity around self-contained knowledge packs.

### What is new

- **Pack flavors** (self-contained by default)
  - Audit pack: `sources/` + `compiled/` + checksums
  - Runtime pack: `compiled/` + checksums (+ signatures placeholder)

- **Pack tooling**
  - `scripts/pack.py verify`
  - `scripts/pack.py build --flavor audit|runtime`

- **Pack spec update**
  - v0.2 rule: a pack must be installable, verifiable, and queryable with no external dependencies

### What stayed the same

- Compiler inputs remain boring and auditable: Markdown or plain text with provenance.
- CI continues to enforce determinism and provenance.
- Runtime layers operate against compiled artifacts, not raw sources.

### Suggested tag

`v0.2.0`
