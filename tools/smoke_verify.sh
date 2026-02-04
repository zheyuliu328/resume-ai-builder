#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[1/4] Python compile"
python3 -m py_compile backend/api_server.py app.py destroy_test.py tools/verify_history.py tools/verify_trim_relevance.py

echo "[2/4] JS syntax"
node -c frontend/app.js frontend/chat.js frontend/import.js

echo "[3/4] History verify"
python3 tools/verify_history.py

echo "[4/4] E2E destroy_test"
python3 destroy_test.py

echo "OK"
