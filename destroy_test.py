#!/usr/bin/env python3
"""End-to-end smoke test (no prompts, minimal output).

Simulates:
  create variant -> select -> save -> JD parse -> JD analyze -> export pdf

This script is intended to be safe to run locally:
- It starts a temporary Flask backend on a random port.
- It writes temporary files (variant + pdf) and cleans them up.

Exit code:
  0 on success, 1 on failure.
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


ROOT_DIR = Path(__file__).resolve().parent


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


def _wait_health(base: str, timeout_s: float = 20.0) -> dict:
    start = time.time()
    last_err: Exception | None = None
    while time.time() - start < timeout_s:
        try:
            return _http_json("GET", f"{base}/health", None, timeout=2.0)
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

    # Track filesystem changes for cleanup.
    data_dir = ROOT_DIR / "data"
    variant_path = data_dir / "variants" / "target_destroy_test.json"
    active_path = data_dir / "active_variant.txt"
    master_path = data_dir / "master.json"
    pdf_path = ROOT_DIR / "destroy_test_output.pdf"

    existed = {
        "variant": variant_path.exists(),
        "active": active_path.exists(),
        "master": master_path.exists(),
        "pdf": pdf_path.exists(),
    }
    prev_active = active_path.read_text(encoding="utf-8") if existed["active"] else None

    try:
        health = _wait_health(base)

        # 1) Save a minimal master resume (ensures /api/variants/create has a source).
        resume_data = {
            "personal": {
                "name": "Destroy Test",
                "email": "destroy.test@example.com",
                "phone": "+86 000 0000 0000",
                "summary": "Smoke test resume data.",
            },
            "education": [],
            "experience": [
                {
                    "company": "ExampleCo",
                    "location": "Remote",
                    "position": "Software Engineer",
                    "period": "2024-2026",
                    "highlights": ["Built APIs", "Improved reliability"],
                }
            ],
            "projects": [],
            "skills": {"languages": "Python, JavaScript"},
        }
        r = _http_json("POST", f"{base}/api/resume", {"resume_data": resume_data}, timeout=10.0)
        if not r.get("success"):
            raise RuntimeError(f"save resume failed: {r}")

        # 2) Create a variant from master.
        r = _http_json(
            "POST",
            f"{base}/api/variants/create",
            {"name": "target_destroy_test", "source": "master"},
            timeout=10.0,
        )
        if not r.get("success"):
            raise RuntimeError(f"create variant failed: {r}")

        # 3) Select the variant.
        r = _http_json("POST", f"{base}/api/variants/select", {"name": "target_destroy_test"}, timeout=10.0)
        if not r.get("success"):
            raise RuntimeError(f"select variant failed: {r}")
        variant_data = r.get("data")
        if not isinstance(variant_data, dict):
            raise RuntimeError("variant select did not return data")

        # 4) Save a small tweak back.
        variant_data.setdefault("personal", {})
        variant_data["personal"]["summary"] = "Updated by destroy_test."
        r = _http_json(
            "POST",
            f"{base}/api/variants/save",
            {"name": "target_destroy_test", "data": variant_data},
            timeout=10.0,
        )
        if not r.get("success"):
            raise RuntimeError(f"save variant failed: {r}")

        # 5) JD parse.
        jd_text = """
ExampleCo is hiring a Software Engineer.
Requirements: Python, JavaScript, REST APIs, testing, performance.
""".strip()
        r = _http_json("POST", f"{base}/api/jd/parse", {"jd": jd_text}, timeout=15.0)
        if not r.get("success"):
            raise RuntimeError(f"jd parse failed: {r}")

        # 6) JD analyze.
        r = _http_json(
            "POST",
            f"{base}/api/jd/analyze",
            {"jd": jd_text, "resume_data": variant_data},
            timeout=20.0,
        )
        if not r.get("success"):
            raise RuntimeError(f"jd analyze failed: {r}")

        # 7) Export PDF (smart fit engine path).
        r = _http_json(
            "POST",
            f"{base}/api/export/pdf",
            {
                "resume_data": variant_data,
                "filename": str(pdf_path.name),
                "target_pages": 1,
                "template": "compact",
            },
            timeout=60.0,
        )
        if not r.get("success"):
            raise RuntimeError(f"export pdf failed: {r}")
        if not pdf_path.exists() or pdf_path.stat().st_size < 1000:
            raise RuntimeError("export pdf did not create a valid file")

        # 8) Confirm export meta persisted in active variant JSON.
        r2 = _http_json("POST", f"{base}/api/variants/select", {"name": "target_destroy_test"}, timeout=10.0)
        if not r2.get("success"):
            raise RuntimeError(f"re-select variant failed: {r2}")
        v2 = r2.get("data")
        exports = None
        if isinstance(v2, dict):
            exports = (v2.get("_meta") or {}).get("exports")
        if not isinstance(exports, list) or not exports:
            raise RuntimeError("expected _meta.exports to be persisted after export")

        meta = r.get("meta") or {}
        print(
            json.dumps(
                {
                    "ok": True,
                    "health_configured": bool(health.get("configured")),
                    "variant": "target_destroy_test",
                    "pdf": str(pdf_path),
                    "pdf_pages": meta.get("pages"),
                    "pdf_trimmed": meta.get("trimmed"),
                    "exports_count": len(exports),
                },
                ensure_ascii=False,
            )
        )
        return 0
    finally:
        # Best-effort shutdown
        proc.terminate()
        try:
            proc.wait(timeout=6)
        except subprocess.TimeoutExpired:
            proc.kill()

        # Cleanup what we created.
        try:
            if not existed["pdf"] and pdf_path.exists():
                pdf_path.unlink()
        except Exception:
            pass
        try:
            if not existed["variant"] and variant_path.exists():
                variant_path.unlink()
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
