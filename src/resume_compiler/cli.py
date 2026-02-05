from __future__ import annotations

import json
from pathlib import Path

import typer
from pydantic import ValidationError

from resume_compiler.domain.schema import Resume

app = typer.Typer(add_completion=False, help="Resume Compiler (CLI-first).")


@app.command()
def validate(profile: Path = typer.Argument(..., exists=True, readable=True)):
    """Validate a profile JSON against the Pydantic schema."""
    try:
        data = json.loads(profile.read_text(encoding="utf-8"))
        Resume.model_validate(data)
    except ValidationError as e:
        typer.echo(e)
        raise typer.Exit(code=2)

    typer.echo("OK")


def main():
    app()


if __name__ == "__main__":
    main()
