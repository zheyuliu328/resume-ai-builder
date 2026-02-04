# TODO

## Approval Gate (Human-in-the-loop)

This repo follows **Local-first + Safety-by-design** (see `VISION.md`).

- **Do not run the worker loop or execute implementation tasks without explicit human approval.**
- Planning, doc updates, and code reading are OK by default.
- Every task below must include a **VERIFY** command so a human can confirm correctness.

---

# Operation V1.0 Polish

> Goal: Make V1.0 shippable (stable, clean, documented) without over-design.
> Rule: Each task must include a VERIFY step (smoke test / lint / script run).

- [x] Task 1: Global cleanup — remove noisy debug logs (console.log / print) and dead code.
  - VERIFY: run `python3 -m py_compile backend/api_server.py app.py` and `node -c frontend/app.js frontend/chat.js frontend/import.js`

- [x] Task 2: Add basic lint discipline (lightweight).
  - Python: add ruff (or pylint if already preferred) config; fix high-severity issues.
  - JS: add eslint config if missing; fix high-severity issues.
  - VERIFY: run lint commands and ensure no "error"-level findings.

- [x] Task 3: Add an end-to-end smoke script `destroy_test.py`.
  - Simulate: create variant -> select -> save -> JD parse -> JD analyze -> export pdf (target_pages=1, template=compact)
  - VERIFY: script exits 0 and logs a minimal success summary.

- [x] Task 4: If Task 3 fails, iterate to fix until it passes.
  - VERIFY: rerun `destroy_test.py`.

- [x] Task 5: Update README.md for Beta 0.9.
  - Document: setup, limitations (text-based PDF import), JD Killer workflow, Smart PDF (fit engine + TRIMMED), watchdog note.
  - VERIFY: README is consistent with current endpoints and UI.

---

# V1.1 (Plan) — High-leverage, minimal dependency creep

## Biggest gaps vs `VISION.md` (Reality check)

1) **Preview → Apply is not consistently enforced**
   - `POST /api/update` writes to `resume_data.json` immediately via `builder._save_resume()`.
   - Chat refine follows preview/apply (good), but update/translate/export paths are mixed.

2) **Data layer versioning/rollback is incomplete**
   - Variants exist (`data/master.json`, `data/variants/*.json`, `active_variant.txt`) but there is **no snapshot history** or rollback mechanism per variant.

3) **“Evidence chain” for targets is partial**
   - JD parse + analysis is stored in `_meta` for newly created targets, but:
     - export metadata/history is not persisted per target
     - there is no standardized schema for “what changed / when / why”

4) **Trim is sequential, not relevance-based**
   - Smart PDF trimming currently drops experiences/bullets by position (`max_experiences`, `max_bullets`) rather than JD relevance.

5) **Export cockpit is minimal**
   - UI has pages/template toggles and download, but lacks:
     - export history
     - explicit warnings/explanations when TRIMMED happens
     - repeatable “export profile” per target

## Proposed tasks (5–8) for V1.1

> Constraints honored: no big rewrites, no heavy frameworks, local-first, verifiable.

- [ ] Task 1: Enforce Preview → Apply semantics for write paths (start with `/api/update`).
  - Change `/api/update` to support `apply=false` (default) returning a suggested `resume_data` without saving.
  - Add `/api/update/apply` or `apply=true` to persist only on explicit action.
  - Frontend: align button labels (“Generate suggestion” vs “Apply/Save”).
  - VERIFY: `python3 -m py_compile backend/api_server.py app.py` and run `python3 destroy_test.py`.

- [ ] Task 2: Add per-variant snapshot history (local, lightweight) + rollback endpoint.
  - On every `/api/variants/save` (and on master save), write a timestamped snapshot under `data/history/<variant>/<ts>.json`.
  - Add endpoints:
    - `GET /api/variants/history?name=...&limit=...`
    - `POST /api/variants/rollback` (explicit) to restore a chosen snapshot.
  - VERIFY: `python3 destroy_test.py` plus a new small script `python3 tools/verify_history.py` (create/save/list/rollback).

- [ ] Task 3: Persist “application evidence chain” in `_meta` (jd_parse/jd_analysis/export meta).
  - Standardize `_meta` schema:
    - `_meta.jd_parse`, `_meta.jd_analysis`, `_meta.jd_text` (already mostly there)
    - `_meta.exports[]`: append `{ts, target_pages, template, pages, trimmed, style, trim, filename}` after each export.
  - Keep local-only; do not store API keys or full PDFs.
  - VERIFY: run `python3 destroy_test.py` and confirm target variant JSON contains `_meta.exports[0]`.

- [ ] Task 4: Relevance-based Trim v0 (no ML; keyword scoring) for Smart PDF.
  - When `_meta.jd_analysis.top_keywords` exists, score experience/project bullets by keyword hits.
  - Update `apply_trim()` to drop lowest-scoring bullets first (instead of purely last N).
  - Keep current CSS fit loop; only improve trim selection.
  - VERIFY: add `python3 tools/verify_trim_relevance.py` that feeds a fake JD analysis + resume and asserts kept bullets include top keywords.

- [ ] Task 5: Export cockpit “explainability” polish (frontend only, minimal UI).
  - In export UI, show:
    - last export meta (pages, template, trimmed yes/no)
    - if trimmed: show a clear warning and link to open the “trim summary” (what was trimmed: counts + categories).
  - VERIFY: `node -c frontend/app.js frontend/chat.js` and manual: export once and see meta rendered.

- [ ] Task 6: Add a single “smoke verify” command that mirrors VISION observability.
  - Create `tools/smoke_verify.sh` (or `python3 tools/smoke_verify.py`) to run:
    - `python3 -m py_compile ...`
    - `python3 destroy_test.py`
    - optional: minimal JS syntax check
  - Document it in README.
  - VERIFY: `bash tools/smoke_verify.sh` exits 0.

- [ ] Task 7: Tighten local-first boundaries + redact logs.
  - Ensure logs never print JD full text or resume full JSON by default (only lengths, hashes, or first line).
  - Add a `LOG_REDACT=1` toggle (default on) for production usage.
  - VERIFY: run `python3 destroy_test.py` and confirm `app.log` does not contain full JD or full resume JSON blobs.

- [ ] Task 8: Add contract tests for “no silent overwrite” invariants.
  - Add a small test script that asserts endpoints that modify data require explicit apply/save.
  - VERIFY: `python3 tools/verify_no_silent_write.py`.
