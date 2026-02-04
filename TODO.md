# Operation V1.0 Polish

> Goal: Make V1.0 shippable (stable, clean, documented) without over-design.
> Rule: Each task must include a VERIFY step (smoke test / lint / script run).

- [ ] Task 1: Global cleanup — remove noisy debug logs (console.log / print) and dead code.
  - VERIFY: run `python3 -m py_compile backend/api_server.py app.py` and `node -c frontend/app.js frontend/chat.js frontend/import.js`

- [ ] Task 2: Add basic lint discipline (lightweight).
  - Python: add ruff (or pylint if already preferred) config; fix high-severity issues.
  - JS: add eslint config if missing; fix high-severity issues.
  - VERIFY: run lint commands and ensure no "error"-level findings.

- [ ] Task 3: Add an end-to-end smoke script `destroy_test.py`.
  - Simulate: create variant -> select -> save -> JD parse -> JD analyze -> export pdf (target_pages=1, template=compact)
  - VERIFY: script exits 0 and logs a minimal success summary.

- [ ] Task 4: If Task 3 fails, iterate to fix until it passes.
  - VERIFY: rerun `destroy_test.py`.

- [ ] Task 5: Update README.md for Beta 0.9.
  - Document: setup, limitations (text-based PDF import), JD Killer workflow, Smart PDF (fit engine + TRIMMED), watchdog note.
  - VERIFY: README is consistent with current endpoints and UI.
