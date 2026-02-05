"""Local-first portfolio site generator.

Generates a static site under data/portfolio_sites/<slug>/.
Privacy by default: redacts contact fields and strips JD-related _meta unless include_contact=True.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict


def slugify(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9._-]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "portfolio"


CONTACT_KEYS = {"email", "phone", "address", "location", "wechat", "linkedin_url"}


def redact_resume(resume_data: Dict[str, Any], include_contact: bool = False) -> Dict[str, Any]:
    data = json.loads(json.dumps(resume_data))  # cheap deep copy

    # Strip JD-related meta unless explicitly needed.
    meta = data.get("_meta")
    if isinstance(meta, dict):
        safe_meta = {k: v for k, v in meta.items() if k not in {"jd_text", "jd_analysis", "jd_parse"}}
        data["_meta"] = safe_meta

    personal = data.get("personal")
    if isinstance(personal, dict) and not include_contact:
        for k in list(personal.keys()):
            if k in CONTACT_KEYS:
                personal[k] = "[Hidden]"

    return data


def generate_site(resume_data: Dict[str, Any], *, slug: str, out_dir: Path, include_contact: bool = False) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)

    safe = redact_resume(resume_data, include_contact=include_contact)

    (out_dir / "assets").mkdir(exist_ok=True)
    (out_dir / "assets" / "style.css").write_text(
        """body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;margin:0;background:#0b1020;color:#e5e7eb}
.wrap{max-width:920px;margin:0 auto;padding:28px}
.card{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.10);border-radius:14px;padding:18px;margin:14px 0}
h1,h2{margin:0 0 10px 0}
.muted{color:rgba(229,231,235,.7)}
ul{margin:8px 0 0 18px}
""",
        encoding="utf-8",
    )

    (out_dir / "resume.json").write_text(json.dumps(safe, ensure_ascii=False, indent=2), encoding="utf-8")

    personal = safe.get("personal") if isinstance(safe.get("personal"), dict) else {}
    name = personal.get("name", "")
    summary = personal.get("summary", personal.get("profile", ""))

    def section(title: str, items_html: str) -> str:
        if not items_html.strip():
            return ""
        return f"<div class='card'><h2>{title}</h2>{items_html}</div>"

    def render_list(items, key_title: str, key_sub: str, key_period: str):
        if not isinstance(items, list) or not items:
            return ""
        parts = []
        for it in items:
            if not isinstance(it, dict):
                continue
            t = it.get(key_title, "")
            sub = it.get(key_sub, "")
            per = it.get(key_period, "")
            highlights = it.get("highlights") if isinstance(it.get("highlights"), list) else []
            li = "".join([f"<li>{h}</li>" for h in highlights if h])
            ul = f"<ul>{li}</ul>" if li else ""
            parts.append(f"<div><div><strong>{t}</strong> <span class='muted'>{sub}</span> <span class='muted' style='float:right'>{per}</span></div>{ul}</div>")
        return "".join(parts)

    edu = render_list(safe.get("education"), "school", "degree", "period")
    exp = render_list(safe.get("experience"), "company", "position", "period")
    proj = render_list(safe.get("projects"), "name", "category", "period")

    html = f"""<!doctype html>
<html lang='en'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width,initial-scale=1'>
  <title>{name or slug}</title>
  <link rel='stylesheet' href='assets/style.css'>
</head>
<body>
  <div class='wrap'>
    <div class='card'>
      <h1>{name or slug}</h1>
      <div class='muted'>Local-first portfolio (privacy-safe by default)</div>
      <p style='margin-top:10px'>{summary or ''}</p>
    </div>
    {section('Experience', exp)}
    {section('Projects', proj)}
    {section('Education', edu)}
    <div class='card muted'>Generated locally. resume.json is redacted by default.</div>
  </div>
</body>
</html>"""

    (out_dir / "index.html").write_text(html, encoding="utf-8")
    return out_dir
