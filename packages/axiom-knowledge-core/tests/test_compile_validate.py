from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from axiom_knowledge_core.compiler import CompileOptions, compile_knowledge
from axiom_knowledge_core.validator import validate_compiled_dir


class TestCompileValidate(unittest.TestCase):
    def test_builtin_compile_and_validate(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            sources = root / "sources"
            out = root / "compiled"
            sources.mkdir()
            (sources / "a.txt").write_text("hello", encoding="utf-8")
            (sources / "b.md").write_text("world", encoding="utf-8")

            compile_knowledge(CompileOptions(sources_dir=sources, out_dir=out, axm_bin=None))
            validate_compiled_dir(out)


if __name__ == "__main__":
    unittest.main()
