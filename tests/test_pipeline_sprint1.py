from __future__ import annotations

from pathlib import Path

from resume_compiler.domain.schema import ResumeContext
from resume_compiler.ingestion.loaders import load_resume
from resume_compiler.pipeline import compile_resume
from resume_compiler.processing.llm_gateway import DummyLLMGateway


def test_compile_resume_smoke(tmp_path: Path):
    profile = {
        "contact": {"name": "A", "email": "a@example.com"},
        "experience": [
            {
                "company": "X",
                "position": "Engineer",
                "location": "HK",
                "period": {"start_date": "2020-01", "end_date": "2021-01", "current": False},
                "raw_highlights": ["Did things"],
                "tech_stack": ["Python"],
            }
        ],
        "skills": ["Python"],
    }

    import json

    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(profile), encoding="utf-8")

    resume = load_resume(profile_path)
    ctx = ResumeContext(target_role="Backend Engineer")

    llm = DummyLLMGateway(
        fixed={
            "experience": [
                {
                    "company": "X",
                    "position": "Engineer",
                    "refined_highlights": ["Improved latency by 20%"],
                }
            ]
        }
    )

    out = compile_resume(resume=resume, ctx=ctx, jd="JD", llm=llm)

    assert out.resume.experience[0].refined_highlights == ["Improved latency by 20%"]
    assert "plan" in out.meta
