from pathlib import Path

from axiom_knowledge_core.compiler import compile_sources
from axiom_knowledge_core.validator import validate_compiled


def test_toy_compile_and_validate(tmp_path: Path) -> None:
    sources = tmp_path / "sources"
    sources.mkdir()
    (sources / "a.txt").write_text("hello", encoding="utf-8")

    out = tmp_path / "compiled"
    compile_sources(sources_dir=sources, out_dir=out)

    errors = validate_compiled(out)
    assert errors == []
