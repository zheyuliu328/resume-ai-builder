#!/usr/bin/env python3
"""Verify relevance-based trimming keeps keyword-rich bullets."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app import trim_resume_relevance  # noqa: E402


def main() -> int:
    resume = {
        "personal": {"name": "T"},
        "education": [],
        "experience": [
            {
                "company": "A",
                "highlights": [
                    "Maintained legacy reporting dashboards.",
                    "Built Python ETL pipelines for JD alignment.",
                    "Wrote documentation.",
                    "Improved REST APIs performance in JavaScript.",
                ],
            }
        ],
        "projects": [
            {
                "name": "P",
                "highlights": [
                    "Random UI tweaks",
                    "Implemented Python data processing",
                    "Added tests",
                ],
            }
        ],
        "skills": {},
    }

    trimmed, summary = trim_resume_relevance(
        resume,
        top_keywords=["python", "rest", "javascript"],
        max_experiences=1,
        max_bullets=2,
    )

    kept = trimmed["experience"][0]["highlights"]
    if len(kept) != 2:
        raise RuntimeError(f"expected 2 kept bullets, got {len(kept)}: {kept}")

    blob = " ".join(kept).lower()
    if "python" not in blob:
        raise RuntimeError(f"expected kept bullets to include 'python', got: {kept}")

    proj_kept = trimmed["projects"][0]["highlights"]
    proj_blob = " ".join(proj_kept).lower()
    if "python" not in proj_blob:
        raise RuntimeError(f"expected project kept highlights to include 'python', got: {proj_kept}")

    if summary.get("mode") != "relevance":
        raise RuntimeError(f"bad summary: {summary}")

    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
