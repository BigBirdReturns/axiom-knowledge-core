from __future__ import annotations

from pathlib import Path

from axiom_knowledge_core.ir.io import read_jsonl


def answer_question(*, compiled_dir: Path, question: str) -> str:
    concepts = read_jsonl(compiled_dir / "concepts.jsonl")
    relations = read_jsonl(compiled_dir / "relations.jsonl")

    q = question.strip().lower()

    if "prereq" in q or "prerequisite" in q:
        return "No prereq relations in compiled artifact." if not relations else _describe_prereqs(concepts, relations)

    return "I cannot answer this question from compiled artifacts yet. Add relations, procedures, and provenance nodes."


def _describe_prereqs(concepts: list[dict], relations: list[dict]) -> str:
    id_to_title = {c["id"]: c.get("title", c["id"]) for c in concepts}
    prereqs = [r for r in relations if r.get("type") == "prereq"]
    if not prereqs:
        return "No prereq relations in compiled artifact."

    lines: list[str] = []
    for r in prereqs:
        lines.append(f"{id_to_title.get(r['dst'], r['dst'])} requires {id_to_title.get(r['src'], r['src'])}")
    return "\n".join(lines)
