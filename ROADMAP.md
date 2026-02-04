# ROADMAP

## V1.1 — Safety & Experience Polish (Local-first)

### High-level goal
Ship a **more controllable, rollbackable, and explainable** local-first resume workflow:
- All mutations are **explicit** (Preview → Apply/Save)
- Every target has a **recoverable history** (snapshots/rollback)
- Exports are **auditable** (export meta + TRIMMED explainability)
- PDF trim chooses **relevance first** (JD-keyword scoring v0)

This milestone optimizes for the North Star in `VISION.md`: fastest/most stable/most controllable local-first system with safety-by-design and observability.

### Scope (in)
1. **Preview → Apply/Save enforcement** across the main write paths (starting with `/api/update`), plus UI wording that matches the mental model.
2. **Per-variant snapshot history + rollback** built on the existing JSON-on-disk variants store (`docs/adr/0001-local-first-json-variants-store.md`).
3. **Evidence chain** stored in each target’s `_meta` (jd_parse/jd_analysis + export metadata/history) and surfaced in the Export UI.
4. **Relevance-based Trim v0** (no ML): use JD analysis keywords to decide what gets trimmed first; provide a trim summary for user trust.

### Non-goals (out)
- No database migration (SQLite/Postgres) and no remote sync (must remain local-first JSON per ADR 0001).
- No login/accounts, collaboration, or social features.
- No heavy new frameworks/dependency creep.
- No “auto-edit & silently overwrite” flows (must remain preview/apply).
- No new major resume features (templates marketplace, ATS scanner, etc.)—polish and safety only.

### Success criteria
- Users can generate suggestions without mutating data until **Apply/Save**.
- Users can list history and rollback a variant locally.
- Each export records an `_meta.exports[]` entry; UI shows last export + TRIMMED warning.
- When JD keywords exist, trim removes least-relevant bullets first and produces a human-readable summary.
