from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from pydantic import ValidationError

from resume_compiler.domain.schema import Resume, ResumeContext
from resume_compiler.ingestion.loaders import load_jd, load_resume
from resume_compiler.pipeline import compile_resume
import os

from resume_compiler.processing.llm_gateway import DummyLLMGateway, OpenAIChatLLMGateway

app = typer.Typer(add_completion=False, help="Resume Compiler (CLI-first).")


@app.command()
def validate(profile: Path = typer.Argument(..., exists=True, readable=True)):
    """Validate a profile JSON/YAML against the Pydantic schema."""
    try:
        load_resume(profile)
    except (ValidationError, ValueError) as e:
        typer.echo(str(e))
        raise typer.Exit(code=2)

    typer.echo("OK")


@app.command()
def compile(
    profile: Path = typer.Argument(..., exists=True, readable=True),
    jd: Path = typer.Argument(..., exists=True, readable=True),
    target_role: str = typer.Option(..., help="Target role/title"),
    out: Optional[Path] = typer.Option(None, help="Write compiled resume JSON to a file"),
):
    """Compile a resume (Sprint 1: deterministic skeleton, dummy LLM)."""

    resume = load_resume(profile)
    jd_text = load_jd(jd)
    ctx = ResumeContext(target_role=target_role)

    llm_mode = os.getenv("RESUME_COMPILER_LLM", "dummy").lower().strip()
    if llm_mode == "real":
        llm = OpenAIChatLLMGateway.from_env()
    else:
        llm = DummyLLMGateway()

    result = compile_resume(resume=resume, ctx=ctx, jd=jd_text, llm=llm)

    payload = {
        "resume": result.resume.model_dump(),
        "meta": result.meta,
    }

    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if out is not None:
        out.write_text(text, encoding="utf-8")
        typer.echo(str(out))
    else:
        typer.echo(text)


def main():
    app()


if __name__ == "__main__":
    main()
