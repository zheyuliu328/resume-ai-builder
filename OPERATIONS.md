# Operations (SOP)

This repo is optimized for **fast local iteration** with **basic governance** so releases remain reproducible.

## Trinity Gate (what it means here)

### 1) Pre-flight (before commit)
- Ensure you are on the right branch: `git status`
- Run quick lint/format checks (if configured):
  - Python: `ruff check .` (and optionally `ruff format .`)
  - Frontend: `npm -C frontend run lint` (if present)

### 2) Verify (before PR)
- Run the repo smoke checks:
  ```bash
  bash tools/smoke_verify.sh
  ```
- If you changed backend logic, run any local scripts under `tools/verify_*.py` that are relevant.

### 3) Audit (continuous)
- CI workflow: `.github/workflows/audit.yml`
  - Python: `pip-audit -r requirements.txt`
  - Node: `npm audit --omit=dev --audit-level=high` (in `frontend/`)

Notes:
- PR audits only run when dependency / workflow files change (path-filtered).
- A weekly scheduled audit still runs regardless.

## Dependency locking

### Python
- Source intent file: `requirements.in`
- Pinned lock: `requirements.txt`

Update flow (simple, local-first):
1. Create/activate a clean venv
2. `pip install -r requirements.in`
3. `pip freeze > requirements.txt`

If maintainability becomes an issue, migrate to `pip-tools` for cleaner diffs.

### Node
- Use `frontend/package-lock.json`.
- Install with `npm ci` for reproducibility.

## Release workflow (GitHub Actions)

Workflow: `.github/workflows/release.yml`

Triggers:
- Push to `main` **only when** the commit message contains `Release vX.Y.Z`.
- Or manual run via `workflow_dispatch` with `version`.

The workflow:
- Creates an annotated git tag `vX.Y.Z`
- Creates a GitHub Release (fails if the release already exists)
- Builds & pushes a Docker image to GHCR

## Common safety rules
- Don’t merge to `main` with a dirty working tree.
- Prefer PRs from `feat/*` branches.
- Keep secrets out of the repo; local data stays local.
