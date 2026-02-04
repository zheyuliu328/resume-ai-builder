"""Local variant storage for resume data.

This is deliberately simple: JSON files on disk under ./data.
Not committed to git (see .gitignore).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


def ensure_dirs(data_dir: Path) -> None:
    (data_dir / 'variants').mkdir(parents=True, exist_ok=True)
    (data_dir / 'history').mkdir(parents=True, exist_ok=True)


def list_variants(data_dir: Path) -> List[str]:
    ensure_dirs(data_dir)
    variants_dir = data_dir / 'variants'
    return sorted([p.stem for p in variants_dir.glob('*.json')])


def load_json(path: Path) -> Dict:
    return json.loads(path.read_text(encoding='utf-8'))


def save_json(path: Path, data: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def get_master_path(data_dir: Path) -> Path:
    return data_dir / 'master.json'


def get_active_variant_path(data_dir: Path) -> Path:
    return data_dir / 'active_variant.txt'


def get_variant_path(data_dir: Path, name: str) -> Path:
    return data_dir / 'variants' / f'{name}.json'


def get_history_dir(data_dir: Path, name: str) -> Path:
    """History directory for a variant (or 'master')."""
    return data_dir / 'history' / name


def write_snapshot(data_dir: Path, name: str, data: Dict, *, ts: str) -> Path:
    """Write a timestamped snapshot for a variant.

    Snapshots are JSON-on-disk for git/diff-friendly rollback.
    Caller provides ts to make tests deterministic.
    """
    ensure_dirs(data_dir)
    d = get_history_dir(data_dir, name)
    d.mkdir(parents=True, exist_ok=True)
    path = d / f'{ts}.json'
    save_json(path, data)
    return path


def list_history(data_dir: Path, name: str, *, limit: int = 20) -> List[str]:
    """Return snapshot timestamps (newest first)."""
    ensure_dirs(data_dir)
    d = get_history_dir(data_dir, name)
    if not d.exists():
        return []
    items = sorted([p.stem for p in d.glob('*.json')], reverse=True)
    if limit and limit > 0:
        return items[: int(limit)]
    return items


def read_active_variant(data_dir: Path) -> Optional[str]:
    p = get_active_variant_path(data_dir)
    if not p.exists():
        return None
    return p.read_text(encoding='utf-8').strip() or None


def write_active_variant(data_dir: Path, name: str) -> None:
    p = get_active_variant_path(data_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(name, encoding='utf-8')
