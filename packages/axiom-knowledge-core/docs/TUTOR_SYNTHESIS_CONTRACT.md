# Tutor Synthesis Contract

The tutor is a renderer over compiled artifacts.

## Allowed outputs

The tutor may output:

- Facts that map to compiled concepts and provenance.
- Procedures that map to compiled procedure nodes (future extension).
- Explanations that only restate or combine compiled statements.

## Prohibited outputs

The tutor must not:

- Introduce a new factual claim that does not map to provenance.
- Guess medical, legal, or safety critical details.
- Hide uncertainty.

## Minimum answer structure

1) Answer
2) Evidence
3) Next steps

## Evidence rules

- Every factual sentence must reference at least one provenance record.
- If coverage is missing, the tutor must say so and propose adjacent topics.

## LLM usage

If a local LLM is used, it is used only for:

- Simplification by reading compiled statements.
- Translation.
- Formatting the answer into age appropriate language.

The LLM is not a knowledge authority.
