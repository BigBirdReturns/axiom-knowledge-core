# Scripts

This directory contains small, pinned helper scripts that support the repository workflow.

These scripts run **before** compilation and enforce the `sources/` input contract.

## Policy gates

- `ci_sources_gate.py`: Enforces allowed file types and required provenance headers in `sources/`.
- `ci_compare_compiled.py`: Compares two compiled output directories and fails if they differ (determinism gate).

## Reference preparation pipelines (optional)

- `html_to_md.py`: Reference HTML to Markdown converter that emits canonical Markdown with required provenance front matter.
- `requirements-prep.txt`: Pinned dependencies for preparation scripts.

These helpers are not part of the compiler. They exist to keep inputs deterministic and PR diffs reviewable.
