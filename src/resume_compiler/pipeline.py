from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from resume_compiler.domain.schema import ExperienceItem, Resume, ResumeContext
from resume_compiler.processing.context_builder import build_prompt
from resume_compiler.processing.llm_gateway import LLMGateway
from resume_compiler.processing.planner import build_plan


@dataclass
class CompileResult:
    resume: Resume
    meta: dict[str, Any]


def compile_resume(*, resume: Resume, ctx: ResumeContext, jd: str, llm: LLMGateway) -> CompileResult:
    """Orchestrate the pipeline.

    Sprint 1 goal: create the stable skeleton (modules, data flow, types).
    Refinement logic will be expanded in later sprints.
    """

    plan = build_plan()
    prompt = build_prompt(resume=resume, ctx=ctx, jd=jd)

    # Minimal structured schema for LLM output in Sprint 1.
    output_schema = {
        "type": "object",
        "properties": {
            "experience": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "company": {"type": "string"},
                        "position": {"type": "string"},
                        "refined_highlights": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["company", "position", "refined_highlights"],
                },
            }
        },
        "required": ["experience"],
    }

    refined = llm.generate_json(system=prompt.system, user=prompt.user, schema=output_schema)

    exp_by_key = {
        (e.company, e.position): e
        for e in resume.experience
    }

    for item in refined.get("experience", []) or []:
        key = (item.get("company"), item.get("position"))
        if key in exp_by_key:
            exp: ExperienceItem = exp_by_key[key]
            rh = item.get("refined_highlights")
            if isinstance(rh, list) and all(isinstance(x, str) for x in rh):
                exp.refined_highlights = rh

    # Re-validate to ensure type safety post mutation
    resume = Resume.model_validate(resume.model_dump())

    return CompileResult(
        resume=resume,
        meta={
            "plan": plan.steps,
            "llm": llm.__class__.__name__,
        },
    )
