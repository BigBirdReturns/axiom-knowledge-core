from __future__ import annotations

from pathlib import Path
from typing import Iterable, TypeVar

import orjson

T = TypeVar("T")


def write_jsonl(path: Path, records: Iterable[object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        for r in records:
            f.write(orjson.dumps(r, option=orjson.OPT_SORT_KEYS))
            f.write(b"\n")


def read_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    with path.open("rb") as f:
        for line in f:
            if not line.strip():
                continue
            out.append(orjson.loads(line))
    return out
