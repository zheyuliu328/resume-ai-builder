from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from resume_compiler.domain.schema import Resume


def load_profile(path: Path) -> dict[str, Any]:
    """Load a raw profile from JSON or YAML."""
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")

    if suffix in {".yaml", ".yml"}:
        data = yaml.safe_load(text)
    elif suffix == ".json":
        data = json.loads(text)
    else:
        raise ValueError(f"Unsupported profile format: {suffix}. Use .json/.yaml")

    if not isinstance(data, dict):
        raise ValueError("Profile must parse to a JSON object / YAML mapping")

    return data


def load_resume(path: Path) -> Resume:
    """Load and validate a profile into the domain model."""
    raw = load_profile(path)
    return Resume.model_validate(raw)


def load_jd(path: Path) -> str:
    """Load a job description (plain text/markdown)."""
    return path.read_text(encoding="utf-8").strip()
