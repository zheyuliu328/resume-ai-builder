# ADR 0002: Manual-gated Release Automation (GitHub Actions + GHCR)

- **Status:** Accepted
- **Date:** 2026-02-05

## Context
We want a lightweight “logistics pipeline” for creating releases and publishing a Docker image to GitHub Container Registry (GHCR).

Constraints:
- **Safety / least-privilege:** avoid long-lived secrets; use `GITHUB_TOKEN` only.
- **Human-gated:** release automation must not run on every merge by accident.
- **No feature creep:** keep this purely as packaging/logistics; no cloud sync/login.
- **Local-first product:** the app remains local-first; the container is just a distribution option.

## Decision
Implement a GitHub Actions workflow that runs **only when explicitly triggered**:

1) **Manual trigger (`workflow_dispatch`)**
   - Operator provides `version = X.Y.Z`.

2) **Commit-message gate on `main`**
   - On `push` to `main`, the workflow proceeds **only if** the head commit message contains `Release vX.Y.Z`.

When triggered, the workflow will:
- Create an annotated git tag `vX.Y.Z`.
- Create a GitHub Release (notes from `RELEASE_NOTES_vX.Y.Z.md` if present; otherwise best-effort extract from `ROADMAP.md`).
- Build and push a Docker image to `ghcr.io/<owner>/<repo>` with tags `vX.Y.Z` and `latest`.

Permissions:
- Default workflow permissions are set to `contents: read`.
- The release job elevates to `contents: write` and `packages: write` (minimum needed to tag/release and push to GHCR).

## Consequences
### Positive
- Prevents accidental releases: requires explicit operator intent.
- No additional secrets management: relies on GitHub-provided `GITHUB_TOKEN`.
- Keeps packaging logic auditable in-repo.

### Negative / Tradeoffs
- A push to `main` still schedules the workflow, but the release job is skipped unless the commit message gate matches.
- Tagging and release creation are centralized in CI; local tags are not the source of truth.

### Notes
- We intentionally avoid automatic releases on every tag push to reduce foot-guns.
- If future needs demand stricter controls, we can add environment protection rules or required reviewers for `workflow_dispatch` runs.