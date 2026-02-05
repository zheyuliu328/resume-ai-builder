"""Diplomat: cover letter + cold email generator.

Preview-first by default. When apply=True, writes to data/diplomat/<slug>/.
If no API key configured, uses deterministic templates.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple


def _tone_for_jd(jd_text: str) -> str:
    t = (jd_text or "").lower()
    if "fast" in t or "scrappy" in t or "seed" in t or "startup" in t:
        return "startup"
    return "formal"


def generate_offline(resume_data: Dict[str, Any], jd_text: str) -> Tuple[str, str, Dict[str, Any]]:
    personal = resume_data.get("personal") if isinstance(resume_data.get("personal"), dict) else {}
    name = personal.get("name") or "Candidate"
    tone = _tone_for_jd(jd_text)

    if tone == "startup":
        cover = f"""# Cover Letter\n\nHi team,\n\nI'm {name}. I like shipping end-to-end and iterating fast with real users. Based on the JD, I can own features across frontend + backend, deliver measurable outcomes, and keep the codebase maintainable.\n\nBest,\n{name}\n"""
        email = f"""Subject: Full-stack builder — fast iteration + ownership\n\nHi team,\n\nI'm {name}. I'm excited about building and shipping quickly. If you're looking for someone who can own features end-to-end and collaborate closely with users, I'd love to chat.\n\nBest,\n{name}\n"""
    else:
        cover = f"""# Cover Letter\n\nDear Hiring Manager,\n\nMy name is {name}. I am applying for this role because it aligns with my experience in building reliable systems and delivering measurable results. Based on the job description, I can contribute across system design, execution, and operational excellence.\n\nSincerely,\n{name}\n"""
        email = f"""Subject: Application — {name}\n\nDear Hiring Manager,\n\nI am {name} and I am interested in the role described. I believe my background aligns well with the requirements, and I would welcome the opportunity to discuss how I can contribute.\n\nSincerely,\n{name}\n"""

    meta = {"tone": tone, "offline": True}
    return cover, email, meta


def save_bundle(out_dir: Path, cover_md: str, email_md: str, meta: Dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "cover_letter.md").write_text(cover_md, encoding="utf-8")
    (out_dir / "cold_email.md").write_text(email_md, encoding="utf-8")
    (out_dir / "_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
