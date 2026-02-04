# ADR 0001: Local-first JSON Variants Store (vs SQLite)

- **Status:** Accepted
- **Date:** 2026-02-04

## Context
We need a reliable, local-first persistence layer for resume data that supports:
- Multiple resume variants (master + targets)
- Fast iteration and easy debugging during early product stages
- Clear rollback / versioning semantics (git-friendly)
- Minimal operational complexity for local deployment (no DB setup)

Alternatives considered:
1) SQLite (single-file DB)
2) JSON files on disk (one file per variant) + a small index (active variant)

## Decision
Use a **local JSON-on-disk variants store** under `./data` (gitignored), with:
- `master.json` as the canonical base
- `variants/<name>.json` (or equivalent) for targets
- An `active` marker file to track current selection

Keep the API surface explicit (`/api/variants`, `/select`, `/create`, `/save`) so the UI can reflect the user’s mental model and provide safe switching / rollback.

## Consequences
### Positive
- Zero external dependencies; works out of the box locally
- Git/diff-friendly for debugging and manual recovery
- Easy to reason about “what changed” per variant
- Aligns with Local-first + Minimalism principles

### Negative / Tradeoffs
- Concurrency is limited (file-level race potential); acceptable for single-user local app
- Scaling to multi-user/server deployments would require redesign (likely DB)
- Large resumes may increase file size and IO overhead (still acceptable at this stage)

### Notes
- Future improvement: add snapshot history per variant (time-stamped JSON) to enable in-app rollback.
- If/when we need multi-user or remote deployments, re-evaluate SQLite/Postgres with migration plan.
