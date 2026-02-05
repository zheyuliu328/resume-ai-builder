"""Local-first Applications (Campaign Objects).

Application binds:
- a JD capture (data/jd_captures/<capture_id>.json)
- a dedicated resume variant (data/master.json + variants/<name>.json)
- a status machine (draft -> ready -> applied -> archived)

Storage:
- data/applications/app_<uuid>.json

Design goals:
- local-first, gitignored data/
- UUID identity to avoid conflicts
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


STATUSES = {"draft", "ready", "applied", "archived"}


@dataclass
class Application:
    id: str
    created_at: str
    status: str
    jd_capture_id: str
    variant_name: str
    meta: Dict[str, Any]


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def new_id() -> str:
    return str(uuid.uuid4())


def app_path(data_dir: Path, app_id: str) -> Path:
    return (data_dir / "applications" / f"app_{app_id}.json")


def ensure_app_dirs(data_dir: Path) -> None:
    (data_dir / "applications").mkdir(parents=True, exist_ok=True)


def create_application(
    data_dir: Path,
    *,
    jd_capture_id: str,
    variant_name: str,
    status: str = "draft",
    meta: Optional[Dict[str, Any]] = None,
) -> Application:
    if status not in STATUSES:
        status = "draft"

    ensure_app_dirs(data_dir)

    app_id = new_id()
    app = Application(
        id=app_id,
        created_at=_now_iso(),
        status=status,
        jd_capture_id=jd_capture_id,
        variant_name=variant_name,
        meta=meta or {},
    )

    p = app_path(data_dir, app_id)
    p.write_text(json.dumps(asdict(app), ensure_ascii=False, indent=2), encoding="utf-8")
    return app


def load_application(data_dir: Path, app_id: str) -> Application:
    p = app_path(data_dir, app_id)
    obj = json.loads(p.read_text("utf-8"))
    return Application(
        id=obj["id"],
        created_at=obj.get("created_at") or _now_iso(),
        status=obj.get("status") or "draft",
        jd_capture_id=obj.get("jd_capture_id") or "",
        variant_name=obj.get("variant_name") or "master",
        meta=obj.get("meta") if isinstance(obj.get("meta"), dict) else {},
    )


def save_application(data_dir: Path, app: Application) -> None:
    ensure_app_dirs(data_dir)
    p = app_path(data_dir, app.id)
    p.write_text(json.dumps(asdict(app), ensure_ascii=False, indent=2), encoding="utf-8")


def set_status(data_dir: Path, app_id: str, status: str) -> Application:
    app = load_application(data_dir, app_id)
    if status in STATUSES:
        app.status = status
        save_application(data_dir, app)
    return app
