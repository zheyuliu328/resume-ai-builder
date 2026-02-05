"""Gap analysis engine (JD vs Resume).

V0 goals:
- Local-first, deterministic, no external calls
- Robust keyword matching for English (simple stemming)
- Provide:
  - keywords (weighted)
  - matches / gaps
  - a trim_suggestions structure usable by UI/Chat

Notes:
- This is intentionally lightweight. Avoid heavy NLP deps.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List, Tuple


WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9+./_-]{2,}")


def _stem_en(token: str) -> str:
    """Very lightweight stemmer.

    Handles common suffixes to reduce false gaps:
    - managing/managed -> manag
    - systems/system -> system

    Pragmatic V0: also strips trailing punctuation and improves plural handling.
    """
    t = (token or "").lower().strip()

    # strip common trailing punctuation (keep internal / + . for tokens like ci/cd, c++).
    t = t.strip("\"'`()[]{}<>.,;:!?")

    # normalize possessive
    if t.endswith("'s"):
        t = t[:-2]

    # common suffixes (adverbs)
    for suf in ("ingly", "edly"):
        if t.endswith(suf) and len(t) > len(suf) + 2:
            return t[: -len(suf)]

    # verbs
    for suf in ("ing", "ed"):
        if t.endswith(suf) and len(t) > len(suf) + 2:
            t = t[: -len(suf)]
            break

    # plurals: prefer stripping only trailing 's' unless it's a classic -es plural.
    if t.endswith("es") and len(t) > 4:
        if t.endswith(("ches", "shes", "xes", "zes", "sses")):
            t = t[:-2]
        else:
            # pipelines -> pipeline (strip only 's')
            t = t[:-1]
    elif t.endswith("s") and len(t) > 3:
        t = t[:-1]

    return t


def _tokens_en(text: str) -> List[str]:
    return [m.group(0) for m in WORD_RE.finditer(text or "")]


def extract_keywords(jd_text: str, *, limit: int = 24) -> List[Dict[str, Any]]:
    toks = _tokens_en(jd_text)
    stems = [_stem_en(t) for t in toks]

    stop = {
        "the",
        "and",
        "with",
        "for",
        "you",
        "your",
        "are",
        "will",
        "this",
        "that",
        "have",
        "from",
        "role",
        "team",
        "years",
        "year",
        "plus",
    }

    stems = [s for s in stems if s not in stop and len(s) >= 3]

    c = Counter(stems)
    out = []
    for k, v in c.most_common(limit):
        out.append({"token": k, "weight": int(v)})
    return out


def resume_blob(resume_data: Dict[str, Any]) -> str:
    # Convert resume json to a flat-ish text blob without leaking entire _meta
    def _walk(x) -> List[str]:
        parts = []
        if isinstance(x, dict):
            for k, v in x.items():
                if k == "_meta":
                    continue
                parts.extend(_walk(v))
        elif isinstance(x, list):
            for it in x:
                parts.extend(_walk(it))
        elif isinstance(x, str):
            parts.append(x)
        return parts

    return "\n".join(_walk(resume_data or {}))


def gap_analyze(jd_text: str, resume_data: Dict[str, Any], *, top_keywords: List[str] = None) -> Dict[str, Any]:
    # keywords source: if provided (e.g., from _meta.jd_analysis.top_keywords), use it.
    if top_keywords and isinstance(top_keywords, list) and top_keywords:
        keys = [str(x) for x in top_keywords if x]
        # normalize to stems
        kw = [{"token": _stem_en(k), "weight": 1, "source": "jd_analysis"} for k in keys][:24]
    else:
        kw = [dict(x, source="extract") for x in extract_keywords(jd_text, limit=24)]

    blob = resume_blob(resume_data)
    resume_stems = {_stem_en(t) for t in _tokens_en(blob)}

    matches = []
    gaps = []
    for item in kw:
        tok = item.get("token")
        if not tok:
            continue
        if tok in resume_stems:
            matches.append(tok)
        else:
            gaps.append(tok)

    # suggestions (very naive): map infra/ops keywords to skills/experience, else projects
    def _section_hint(t: str) -> str:
        infra = {"kubernet", "docker", "linux", "network", "observ", "kafka", "flink"}
        data = {"sql", "statist", "experiment", "dashboard", "metric"}
        if any(t.startswith(x) for x in infra):
            return "experience"
        if any(t.startswith(x) for x in data):
            return "projects"
        return "skills"

    suggestions = [
        {
            "gap": g,
            "suggest_section": _section_hint(g),
            "instruction": f"Add evidence for '{g}' into the most relevant { _section_hint(g) } entry. Keep it factual and quantified if possible.",
        }
        for g in gaps[:12]
    ]

    return {
        "keywords": kw,
        "matches": matches,
        "gaps": gaps,
        "suggestions": suggestions,
    }
