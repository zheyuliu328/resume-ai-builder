#!/usr/bin/env python3
"""Verify per-variant history + rollback.

Runs a tiny end-to-end sequence against a temporary backend:
  - save master
  - create/select variant
  - save variant twice (creates 2 snapshots)
  - list history
  - rollback to the older snapshot and confirm data restored

Exit 0 on success.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent


def _pick_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _http_json(method: str, url: str, payload: dict | None = None, timeout: float = 10.0) -> dict:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code} for {url}: {body}") from e


def _wait_health(base: str, timeout_s: float = 20.0) -> None:
    start = time.time()
    last_err: Exception | None = None
    while time.time() - start < timeout_s:
        try:
            r = _http_json("GET", f"{base}/health", None, timeout=2.0)
            if r.get("status") == "ok":
                return
        except Exception as e:
            last_err = e
            time.sleep(0.3)
    raise RuntimeError(f"Backend did not become healthy within {timeout_s}s: {last_err}")


def main() -> int:
    port = _pick_port()
    base = f"http://127.0.0.1:{port}"

    env = os.environ.copy()
    env["FLASK_PORT"] = str(port)
    env.setdefault("LOG_LEVEL", "WARNING")
    env.setdefault("FLASK_DEBUG", "0")

    backend_cmd = [sys.executable, str(ROOT_DIR / "backend" / "api_server.py")]
    proc = subprocess.Popen(
        backend_cmd,
        cwd=str(ROOT_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    data_dir = ROOT_DIR / "data"
    variant_name = "target_history_test"
    variant_path = data_dir / "variants" / f"{variant_name}.json"
    active_path = data_dir / "active_variant.txt"
    master_path = data_dir / "master.json"
    history_dir = data_dir / "history" / variant_name

    existed = {
        "variant": variant_path.exists(),
        "active": active_path.exists(),
        "master": master_path.exists(),
        "history": history_dir.exists(),
    }
    prev_active = active_path.read_text(encoding="utf-8") if existed["active"] else None

    try:
        _wait_health(base)

        # Save master so we can create variant.
        resume_data = {
            "personal": {"name": "History Test", "summary": "v0"},
            "education": [],
            "experience": [],
            "projects": [],
            "skills": {},
        }
        r = _http_json("POST", f"{base}/api/resume", {"resume_data": resume_data}, timeout=10.0)
        if not r.get("success"):
            raise RuntimeError(f"save master failed: {r}")

        # Create + select variant.
        r = _http_json(
            "POST",
            f"{base}/api/variants/create",
            {"name": variant_name, "source": "master"},
            timeout=10.0,
        )
        if not r.get("success"):
            raise RuntimeError(f"create variant failed: {r}")

        r = _http_json("POST", f"{base}/api/variants/select", {"name": variant_name}, timeout=10.0)
        if not r.get("success"):
            raise RuntimeError(f"select variant failed: {r}")
        data = r.get("data")
        if not isinstance(data, dict):
            raise RuntimeError("variant select did not return data")

        # Save twice => 2 snapshots.
        data.setdefault("personal", {})
        data["personal"]["summary"] = "v1"
        r = _http_json("POST", f"{base}/api/variants/save", {"name": variant_name, "data": data}, timeout=10.0)
        if not r.get("success"):
            raise RuntimeError(f"save v1 failed: {r}")

        data["personal"]["summary"] = "v2"
        r = _http_json("POST", f"{base}/api/variants/save", {"name": variant_name, "data": data}, timeout=10.0)
        if not r.get("success"):
            raise RuntimeError(f"save v2 failed: {r}")

        # List history and pick the older snapshot.
        r = _http_json("GET", f"{base}/api/variants/history?name={variant_name}&limit=10", None, timeout=10.0)
        if not r.get("success"):
            raise RuntimeError(f"history list failed: {r}")

        items = r.get("history")
        if not isinstance(items, list) or len(items) < 2:
            raise RuntimeError(f"expected >=2 history items, got: {items}")

        newest = items[0].get("ts")
        older = items[1].get("ts")
        if not newest or not older:
            raise RuntimeError(f"bad history payload: {items}")

        # Rollback to older, ensure summary == v1.
        r = _http_json("POST", f"{base}/api/variants/rollback", {"name": variant_name, "ts": older}, timeout=10.0)
        if not r.get("success"):
            raise RuntimeError(f"rollback failed: {r}")

        rolled = r.get("data")
        if not isinstance(rolled, dict):
            raise RuntimeError("rollback did not return data")
        summary = (rolled.get("personal") or {}).get("summary")
        if summary != "v1":
            raise RuntimeError(f"rollback mismatch: expected v1, got {summary!r}")

        print(json.dumps({"ok": True, "variant": variant_name, "snapshots": [newest, older]}, ensure_ascii=False))
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=6)
        except subprocess.TimeoutExpired:
            proc.kill()

        # Cleanup best-effort.
        try:
            if not existed["variant"] and variant_path.exists():
                variant_path.unlink()
        except Exception:
            pass
        try:
            if not existed["history"] and history_dir.exists():
                for p in history_dir.glob("*.json"):
                    try:
                        p.unlink()
                    except Exception:
                        pass
                try:
                    history_dir.rmdir()
                except Exception:
                    pass
        except Exception:
            pass
        try:
            if not existed["active"]:
                if active_path.exists():
                    active_path.unlink()
            else:
                if prev_active is not None:
                    active_path.write_text(prev_active, encoding="utf-8")
        except Exception:
            pass
        try:
            if not existed["master"] and master_path.exists():
                master_path.unlink()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
