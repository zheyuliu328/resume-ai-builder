#!/usr/bin/env python3
"""Verify Data Refinery (local-first analytics) without API keys.

This script reads the local JSON variants store under ./data and prints:
- number of target variants
- average match_score (if present)
- most common gaps / top_keywords

It is intentionally dependency-free.

Usage:
  python3 tools/verify_refinery.py
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    master_path = DATA / "master.json"
    variants_dir = DATA / "variants"

    variants = []
    if variants_dir.exists():
        variants = sorted([p.stem for p in variants_dir.glob("*.json")])

    names = ["master"] + variants

    match_scores = []
    gaps_counter: Counter = Counter()
    kw_counter: Counter = Counter()

    def iter_data(name: str) -> dict:
        if name == "master":
            return load_json(master_path) if master_path.exists() else {}
        p = variants_dir / f"{name}.json"
        return load_json(p) if p.exists() else {}

    per_variant = []
    for name in names:
        data = iter_data(name)
        meta = data.get("_meta") if isinstance(data, dict) else None
        meta = meta if isinstance(meta, dict) else {}
        jd = meta.get("jd_analysis") if isinstance(meta, dict) else None
        jd = jd if isinstance(jd, dict) else {}

        ms = jd.get("match_score")
        if isinstance(ms, (int, float)):
            match_scores.append(float(ms))

        gaps = jd.get("gaps")
        if isinstance(gaps, list):
            gaps_counter.update([str(x).strip().lower() for x in gaps if str(x).strip()])

        kws = jd.get("top_keywords")
        if isinstance(kws, list):
            kw_counter.update([str(x).strip().lower() for x in kws if str(x).strip()])

        per_variant.append(
            {
                "name": name,
                "match_score": ms if isinstance(ms, (int, float)) else None,
                "gaps_count": len(gaps) if isinstance(gaps, list) else 0,
                "keywords_count": len(kws) if isinstance(kws, list) else 0,
                "exports_count": len(meta.get("exports")) if isinstance(meta.get("exports"), list) else 0,
            }
        )

    stats = {
        "targets_count": len(variants),
        "variants_total": len(names),
        "avg_match_score": round(mean(match_scores), 2) if match_scores else None,
        "top_gaps": gaps_counter.most_common(10),
        "top_keywords": kw_counter.most_common(10),
        "per_variant": per_variant,
    }

    print("[Refinery] Local-first analytics summary")
    print(json.dumps(stats, ensure_ascii=False, indent=2))

    # Non-fatal if no data exists.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
