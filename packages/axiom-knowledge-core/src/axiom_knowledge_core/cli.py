from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from axiom_knowledge_core.compiler import CompileOptions, compile_knowledge
from axiom_knowledge_core.qa import answer_question
from axiom_knowledge_core.validator import ValidationError, validate_compiled_dir

app = typer.Typer(add_completion=False)
console = Console()


@app.command()
def compile(
    sources: Path = typer.Option(..., "--sources", exists=True, file_okay=False, dir_okay=True),
    out: Path = typer.Option(..., "--out", file_okay=False, dir_okay=True),
    axm_bin: str | None = typer.Option(None, "--axm-bin", help="Optional path to axm binary"),
) -> None:
    """Compile sources into compiled artifacts."""
    out_dir = compile_knowledge(CompileOptions(sources_dir=sources, out_dir=out, axm_bin=axm_bin))
    console.print(f"Compiled artifacts written to: {out_dir}")


@app.command()
def validate(
    compiled: Path = typer.Option(..., "--compiled", exists=True, file_okay=False, dir_okay=True),
) -> None:
    """Validate a compiled artifact directory."""
    try:
        validate_compiled_dir(compiled)
    except ValidationError as e:
        console.print(f"[bold red]Validation failed[/bold red]: {e}")
        raise typer.Exit(code=1)
    console.print("[bold green]Validation passed[/bold green]")


@app.command()
def qa(
    compiled: Path = typer.Option(..., "--compiled", exists=True, file_okay=False, dir_okay=True),
    question: str = typer.Option(..., "--question"),
) -> None:
    """Answer a question using compiled artifacts only."""
    console.print(answer_question(compiled_dir=compiled, question=question))
