#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Clean Start Protocol
# lsof may be unavailable; best-effort kill any dev server running api_server.
if command -v pkill >/dev/null 2>&1; then
  pkill -f "backend/api_server.py" >/dev/null 2>&1 || true
fi

echo "[1/5] Python compile"
python3 -m py_compile \
  backend/api_server.py app.py destroy_test.py \
  backend/application_store.py backend/gap_engine.py \
  tools/verify_history.py tools/verify_trim_relevance.py tools/verify_gap_engine.py

echo "[2/5] JS syntax"
node -c frontend/app.js frontend/chat.js frontend/import.js frontend/mission.js

echo "[3/5] History verify"
python3 tools/verify_history.py

echo "[4/5] Gap engine verify"
python3 tools/verify_gap_engine.py

echo "[5/5] E2E destroy_test"
python3 destroy_test.py

echo "OK"
