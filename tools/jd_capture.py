"""Scout capture: store JD captures locally under data/jd_captures/*.json."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


@dataclass
class Capture:
    ts: str
    url: str
    title: str
    text: str
    html: str = ""


def save_capture(base_dir: Path, payload: Dict[str, Any]) -> Path:
    base_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S%fZ")
    cap = Capture(
        ts=ts,
        url=str(payload.get("url") or "").strip(),
        title=str(payload.get("title") or "").strip(),
        text=str(payload.get("text") or "").strip(),
        html=str(payload.get("html") or "").strip(),
    )

    path = base_dir / f"{ts}.json"
    path.write_text(json.dumps(asdict(cap), ensure_ascii=False, indent=2), encoding="utf-8")
    return path
