from __future__ import annotations

from dataclasses import dataclass

from resume_compiler.domain.schema import Resume, ResumeContext


@dataclass(frozen=True)
class PromptContext:
    system: str
    user: str


def build_prompt(*, resume: Resume, ctx: ResumeContext, jd: str) -> PromptContext:
    """Build a prompt bundle.

    Sprint 1: keep it straightforward, deterministic, and schema-driven.
    """

    system = (
        "You are a resume compilation engine. "
        "Return structured JSON only. Do not hallucinate."
    )

    user = (
        f"Target role: {ctx.target_role}\n"
        f"Language: {ctx.language}\n"
        f"Tone: {ctx.tone}\n\n"
        "Job description:\n"
        f"{jd}\n\n"
        "Candidate resume (structured):\n"
        f"{resume.model_dump_json(indent=2)}\n"
    )

    return PromptContext(system=system, user=user)
