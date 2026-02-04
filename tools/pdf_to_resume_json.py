#!/usr/bin/env python3
"""Convert a text-based resume PDF into this project's resume_data JSON schema.

Goal (Phase 1 / PR3): get *usable structured data* from an existing PDF resume.

Notes:
- This script assumes the PDF contains extractable text (not scanned images).
- OCR is intentionally out-of-scope for Phase 1.
- If CLAUDE_API_KEY is set, an optional AI refinement step can be enabled later.

Usage:
  python3 tools/pdf_to_resume_json.py --in /path/to/resume.pdf --out resume_data.imported.json

"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List

import PyPDF2


SCHEMA_TEMPLATE = {
    "personal": {"name": "", "email": "", "phone": "", "summary": "", "linkedin": "", "linkedin_url": ""},
    "education": [],
    "experience": [],
    "projects": [],
    "skills": {},
}


SECTION_ALIASES: Dict[str, List[str]] = {
    "profile": ["profile", "summary", "about"],
    "education": ["education", "education experience", "academic"],
    "experience": ["experience", "work experience", "professional experience", "employment"],
    "projects": ["projects", "project experience"],
    "skills": ["skills", "technical skills"],
}


def extract_text(pdf_path: Path) -> str:
    reader = PyPDF2.PdfReader(str(pdf_path))
    parts: List[str] = []
    for page in reader.pages:
        t = page.extract_text() or ""
        parts.append(t)
    text = "\n".join(parts)
    # normalize whitespace
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def find_contact_block(text: str) -> Dict[str, str]:
    personal = dict(SCHEMA_TEMPLATE["personal"])

    # naive patterns
    email = re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, re.I)
    phone = re.search(r"(\+?\d[\d\s\-()]{7,}\d)", text)
    linkedin = re.search(r"linkedin\.com/in/([A-Za-z0-9\-_%]+)", text, re.I)

    if email:
        personal["email"] = email.group(0)
    if phone:
        personal["phone"] = phone.group(0).strip()
    if linkedin:
        personal["linkedin"] = linkedin.group(1)
        personal["linkedin_url"] = f"https://www.linkedin.com/in/{linkedin.group(1)}"

    # name heuristic: first non-empty line that looks like a name
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if lines:
        # avoid picking section headers
        for l in lines[:5]:
            low = re.sub(r"[^a-z]", "", l.lower())
            if any(low == s.replace(" ", "") for group in SECTION_ALIASES.values() for s in group):
                continue
            # avoid lines that look like contact
            if "@" in l or "linkedin" in l.lower():
                continue
            if len(l) <= 60:
                personal["name"] = l
                break

    return personal


def split_sections(text: str) -> Dict[str, str]:
    """Split resume text into section chunks based on headings.

    This is heuristic and language-agnostic-ish (works best for English headings).
    """
    lines = [ln.rstrip() for ln in text.splitlines()]

    # build regex for headings
    heading_to_key: Dict[str, str] = {}
    for key, aliases in SECTION_ALIASES.items():
        for a in aliases:
            heading_to_key[a.lower()] = key

    def normalize_heading(s: str) -> str:
        s2 = re.sub(r"[^A-Za-z ]", "", s).strip().lower()
        s2 = re.sub(r"\s+", " ", s2)
        return s2

    current = "_preamble"
    chunks: Dict[str, List[str]] = {current: []}

    for ln in lines:
        h = normalize_heading(ln)
        if h in heading_to_key:
            current = heading_to_key[h]
            chunks.setdefault(current, [])
            continue
        chunks.setdefault(current, []).append(ln)

    return {k: "\n".join(v).strip() for k, v in chunks.items() if "\n".join(v).strip()}


def parse_skills(skills_text: str) -> Dict[str, str]:
    # simple: keep as one blob for now; later we can categorize with AI
    cleaned = re.sub(r"\s+", " ", skills_text).strip()
    if not cleaned:
        return {}
    return {"skills": cleaned}


def to_json(text: str) -> Dict:
    out = json.loads(json.dumps(SCHEMA_TEMPLATE))

    out["personal"] = find_contact_block(text)
    sections = split_sections(text)

    # profile/summary: take first paragraph from profile section, else fallback to first 3 lines preamble
    profile = sections.get("profile")
    if profile:
        out["personal"]["summary"] = profile.strip()[:1200]

    skills_blob = sections.get("skills")
    if skills_blob:
        out["skills"] = parse_skills(skills_blob)

    # For Phase 1, keep experience/education/projects as raw blocks to be refined via Chat/AI later.
    # This avoids bad auto-structuring.
    if "education" in sections:
        out["education"] = [{"raw": sections["education"]}]
    if "experience" in sections:
        out["experience"] = [{"raw": sections["experience"]}]
    if "projects" in sections:
        out["projects"] = [{"raw": sections["projects"]}]

    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, help="Input PDF path")
    ap.add_argument("--out", dest="out", required=True, help="Output JSON path")
    args = ap.parse_args()

    inp = Path(args.inp).expanduser().resolve()
    outp = Path(args.out).expanduser().resolve()

    if not inp.exists():
        raise SystemExit(f"Input not found: {inp}")

    text = extract_text(inp)
    if not text.strip():
        raise SystemExit("No extractable text found. If this is a scanned PDF, OCR is needed (out of scope for Phase 1).")

    data = to_json(text)
    outp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote: {outp}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
