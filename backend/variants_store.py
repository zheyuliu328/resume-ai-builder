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


def read_active_variant(data_dir: Path) -> Optional[str]:
    p = get_active_variant_path(data_dir)
    if not p.exists():
        return None
    return p.read_text(encoding='utf-8').strip() or None


def write_active_variant(data_dir: Path, name: str) -> None:
    p = get_active_variant_path(data_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(name, encoding='utf-8')
