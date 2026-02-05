"""Text-only mock interviewer (offline rubric).

Stores sessions locally under data/interviews/<session_id>.json.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class QA:
    q: str
    a: str = ""
    feedback: str = ""


@dataclass
class Session:
    id: str
    ts: str
    target: str
    qas: List[QA] = field(default_factory=list)
    idx: int = 0


DEFAULT_QUESTIONS = [
    "Walk me through your most relevant project for this role.",
    "Describe a time you made a tradeoff between speed and correctness.",
    "What metrics would you use to evaluate success in the first 30 days?",
]


def start_session(store_dir: Path, *, target: str = "general") -> Session:
    store_dir.mkdir(parents=True, exist_ok=True)
    sid = str(uuid.uuid4())
    ts = datetime.utcnow().isoformat() + "Z"
    s = Session(id=sid, ts=ts, target=target, qas=[QA(q=q) for q in DEFAULT_QUESTIONS])
    save_session(store_dir, s)
    return s


def load_session(store_dir: Path, session_id: str) -> Session:
    p = store_dir / f"{session_id}.json"
    obj = json.loads(p.read_text("utf-8"))
    qas = [QA(**x) for x in obj.get("qas", [])]
    return Session(id=obj["id"], ts=obj["ts"], target=obj.get("target", "general"), qas=qas, idx=int(obj.get("idx", 0)))


def save_session(store_dir: Path, s: Session) -> None:
    p = store_dir / f"{s.id}.json"
    p.write_text(json.dumps({**asdict(s), "qas": [asdict(x) for x in s.qas]}, ensure_ascii=False, indent=2), encoding="utf-8")


def next_question(s: Session) -> str:
    if s.idx >= len(s.qas):
        return "(Done)"
    return s.qas[s.idx].q


def score_answer(a: str) -> str:
    a = (a or "").strip()
    if len(a) < 60:
        return "Too short. Add specifics, metrics, and concrete actions."
    if any(x in a.lower() for x in ["i did", "i built", "%", "ms", "users", "revenue"]):
        return "Good: includes concrete actions and/or metrics. Consider tightening structure (Situation→Action→Result)."
    return "Okay: add quantified impact and more technical detail where appropriate."


def answer(store_dir: Path, session_id: str, text: str) -> Dict[str, Any]:
    s = load_session(store_dir, session_id)
    if s.idx >= len(s.qas):
        return {"done": True}
    s.qas[s.idx].a = text
    s.qas[s.idx].feedback = score_answer(text)
    s.idx += 1
    save_session(store_dir, s)
    return {"done": s.idx >= len(s.qas), "feedback": s.qas[s.idx - 1].feedback}
