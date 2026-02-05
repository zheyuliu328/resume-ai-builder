"""Quick verification for add-ons APIs (no API keys required)."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
BASE = os.environ.get("BASE", "http://127.0.0.1:5001")


def main():
    # Ensure server is up
    try:
        requests.get(BASE + "/health", timeout=2)
    except Exception:
        p = subprocess.Popen([sys.executable, str(ROOT / "backend" / "api_server.py")], cwd=str(ROOT), env={**os.environ, "FLASK_PORT": "5001"})
        time.sleep(1.5)

    # capture
    jd = {"url": "https://example.com", "title": "JD", "text": "startup scrappy fast", "html": "<h1>JD</h1>"}
    r = requests.post(BASE + "/api/jd/capture", json=jd, timeout=5)
    assert r.status_code == 200 and r.json().get("success")

    # diplomat
    r = requests.post(BASE + "/api/diplomat/generate", json={"jd": jd["text"], "apply": False}, timeout=5)
    j = r.json(); assert j.get("success") and j.get("cover_letter")

    # portfolio
    r = requests.post(BASE + "/api/portfolio/generate", json={"slug": "test", "include_contact": False}, timeout=10)
    j = r.json(); assert j.get("success")
    resume_json = Path(j["out_dir"]) / "resume.json"
    data = json.loads(resume_json.read_text("utf-8"))
    personal = data.get("personal", {})
    assert personal.get("email") in (None, "[Hidden]")

    # interview
    r = requests.post(BASE + "/api/interview/start", json={"target": "general"}, timeout=5)
    sid = r.json()["session_id"]
    r = requests.get(BASE + "/api/interview/next", params={"session_id": sid}, timeout=5)
    assert r.json().get("question")
    r = requests.post(BASE + "/api/interview/answer", json={"session_id": sid, "answer": "I built X and improved latency by 30%"}, timeout=5)
    assert r.json().get("feedback")

    print("OK")


if __name__ == "__main__":
    main()
