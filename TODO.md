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

# V1.1 (Plan) — Safety & Experience Polish (no feature bloat)

## Biggest gaps vs `VISION.md` (Reality check)

1) **Preview → Apply is not consistently enforced**
   - Several paths return/transform resume JSON without a single, consistent “suggest vs persist” contract.

2) **Data layer rollback is incomplete**
   - Variants exist (`data/master.json`, `data/variants/*.json`, `active_variant.txt`) but there is **no per-variant snapshot history** and no rollback.

3) **Evidence chain + export explainability are partial**
   - JD parse/analyze exists, but export history and TRIMMED explanations are not first-class.

4) **Trim is sequential, not relevance-based**
   - Smart PDF trimming drops content by position rather than JD relevance.

## Proposed tasks (3–5) for V1.1

> Constraints honored: local-first, minimalism, safety-by-design, and verifiable outcomes.

- [ ] Task 1: Enforce Preview → Apply/Save semantics for mutation paths (start with `/api/update`).
  - Add an explicit `apply` flag (default `false`) so the API can return a **suggested** `resume_data` without persisting.
  - Provide an explicit Apply/Save action (endpoint or flag) that is the **only** persistence path.
  - Frontend: align labels with the mental model (“Preview suggestion” vs “Apply/Save”).
  - VERIFY: `python3 -m py_compile backend/api_server.py app.py` and run `python3 destroy_test.py`.
  - Rationale: `VISION.md` §Safety by design (“所有写入都要有显式触发（Apply/Save）”).

- [ ] Task 2: Add per-variant snapshot history + rollback (JSON-on-disk, local-only).
  - On every variant save, write a timestamped snapshot under `data/history/<variant>/<ts>.json`.
  - Add endpoints:
    - `GET /api/variants/history?name=...&limit=...`
    - `POST /api/variants/rollback` (explicit restore)
  - VERIFY: run `python3 destroy_test.py` plus `python3 tools/verify_history.py` (create/save/list/rollback).
  - Rationale: ADR `docs/adr/0001-local-first-json-variants-store.md` (git-friendly rollback semantics) + `VISION.md` §Local-first/§Safety.

- [ ] Task 3: Persist the “application evidence chain” and export history in `_meta`, and surface it in Export UI.
  - Standardize `_meta` schema for targets:
    - `_meta.jd_parse`, `_meta.jd_analysis`, `_meta.jd_text`
    - `_meta.exports[]`: append `{ts, target_pages, template, pages, trimmed, trim_summary, filename}` per export
  - Export UI: show last export meta and a clear TRIMMED warning when applicable.
  - VERIFY: run `python3 destroy_test.py` and confirm target variant JSON contains `_meta.exports[0]`; JS syntax check: `node -c frontend/app.js frontend/chat.js`.
  - Rationale: `VISION.md` Near-term targets (“投递证据链”“Export Cockpit 更完善”) + §Observability.

- [ ] Task 4: Relevance-based Trim v0 (no ML): trim least-relevant bullets first + produce a trim summary.
  - When `_meta.jd_analysis.top_keywords` exists, score bullets by keyword hits; drop lowest-scoring first.
  - Emit `trim_summary` (counts + categories) so the UI can explain what changed.
  - VERIFY: add `python3 tools/verify_trim_relevance.py` (feeds fake JD analysis + resume; asserts kept bullets include top keywords).
  - Rationale: `VISION.md` Near-term targets (“更智能的 Trim（基于 JD relevance）”) + §Safety (“可解释”).

- [ ] Task 5: One-command smoke verification for key paths.
  - Add `tools/smoke_verify.sh` (or `python3 tools/smoke_verify.py`) to run compile/lint/smoke steps consistently.
  - Document it (briefly) so a human can repeatably verify V1.1.
  - VERIFY: `bash tools/smoke_verify.sh` exits 0.
  - Rationale: `VISION.md` §Observability (“关键路径必须有冒烟测试（smoke test）和可重复验证”).
