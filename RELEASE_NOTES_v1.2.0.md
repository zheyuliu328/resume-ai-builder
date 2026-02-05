# v1.2.0 — The Arsenal (Personal Career Suite)

This release turns Resume AI Builder into a **local-first personal career arsenal**: you can capture JDs, generate targeted variants, export fit-to-page PDFs, generate diplomacy documents, generate a privacy-safe portfolio site, and run text mock interviews — all without leaking your data.

## New: Career Arsenal Add-ons
### Portfolio Generator (#8)
- Generate a **static portfolio site** locally via `POST /api/portfolio/generate`.
- Output: `data/portfolio_sites/<slug>/` (html + css + redacted resume.json by default).
- Privacy-by-default: contact fields are redacted unless explicitly allowed.

### Diplomat (#7)
- Generate **cover letter + cold email** bundles via `POST /api/diplomat/generate`.
- Preview-first by default; `apply=true` writes to `data/diplomat/<slug>/`.
- Offline deterministic templates when no API key.

### Scout (#6)
- Capture job descriptions into a local store via `POST /api/jd/capture`.
- Includes a lightweight bookmarklet (posts to localhost only).
- Stored under `data/jd_captures/*.json`.

### Mock Interviewer (#9)
- Text-only mock interview MVP:
  - `/api/interview/start`, `/api/interview/next`, `/api/interview/answer`
- Sessions stored locally under `data/interviews/`.

## Improvements (Safety + Explainability)
- Preview→Apply discipline for mutation paths.
- Variant history snapshots + rollback support.
- Evidence chain persisted in `_meta` including export history.
- Smart PDF: better relevance-based trimming (v0) + TRIMMED warnings.
- One-command verification: `tools/smoke_verify.sh`.

## Ops / Logistics
- Added GitHub Actions release workflow with least-privilege permissions and explicit release gate.
- Added Dockerfile and README run instructions.

## Non-goals / Guardrails
- No cloud sync, no login.
- No auto-apply automation; autonomous career agent remains design-only with human gates.

## Quick Verify
```bash
bash tools/smoke_verify.sh
```
