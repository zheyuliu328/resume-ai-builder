from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Plan:
    """Execution plan for the compiler pipeline."""

    steps: list[str]


def build_plan() -> Plan:
    # Sprint 1: fixed plan, can later be made adaptive.
    return Plan(
        steps=[
            "validate_inputs",
            "build_prompt",
            "llm_refine_highlights",
            "post_validate",
        ]
    )
