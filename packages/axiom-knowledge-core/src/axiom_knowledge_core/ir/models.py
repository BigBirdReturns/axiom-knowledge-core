from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


RelationType = Literal[
    "prereq",
    "depends_on",
    "explains",
    "contradicts",
    "supports",
    "example_of",
]


class Concept(BaseModel):
    id: str = Field(..., description="Stable concept ID")
    title: str
    summary: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class Relation(BaseModel):
    id: str = Field(..., description="Stable relation ID")
    src: str = Field(..., description="Source concept ID")
    dst: str = Field(..., description="Destination concept ID")
    type: RelationType
    weight: float = 1.0


class Provenance(BaseModel):
    id: str = Field(..., description="Stable provenance ID")
    target_id: str = Field(..., description="Concept or relation ID")
    source_path: str
    source_sha256: str
    locator: dict[str, Any] = Field(
        default_factory=dict,
        description="Span locator. Example: {page: 3, start: 120, end: 220}",
    )
    note: Optional[str] = None


class Manifest(BaseModel):
    schema_version: str = "0.1"
    built_at_utc: str
    tool: str
    tool_version: str
    sources_sha256: dict[str, str]
    outputs_sha256: dict[str, str]
    counts: dict[str, int]
