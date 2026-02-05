# ROADMAP

## V1.1 — Safety & Experience Polish (Local-first)

### High-level goal
Ship a **more controllable, rollbackable, and explainable** local-first resume workflow:
- All mutations are **explicit** (Preview → Apply/Save)
- Every target has a **recoverable history** (snapshots/rollback)
- Exports are **auditable** (export meta + TRIMMED explainability)
- PDF trim chooses **relevance first** (JD-keyword scoring v0)

### Scope (in)
1. Preview → Apply/Save enforcement across main write paths.
2. Per-variant snapshot history + rollback (ADR-0001 compliant).
3. Evidence chain stored in `_meta` incl. exports history.
4. Relevance-based Trim v0 + user-facing trim summary.

### Non-goals (out)
- No DB migration / no cloud sync / no login.
- No heavy dependency creep.

### Success criteria
- Users can preview suggestions without silent mutation.
- Users can rollback variants.
- Export history is persisted and explainable.

---

## V1.3 — Mission Control (The War Room)

### High-level goal
Turn isolated tools into a **feedback control system** by introducing the **Campaign Object (Application)** and a dual-pane War Room UI:
- Sense: Scout/JD capture
- Decide: Gap Engine
- Act: Resume refine + Apply
- Measure: Recompute → gaps turn green

### Scope (in)
- Application object binds **JD capture ↔ dedicated variant ↔ status**.
- Gap Engine v0 (light stemming, no heavy NLP).
- Mission Control UI: grouped Application list + JD gaps/matches + click-to-command.
- Clean Start Protocol baked into smoke verification to avoid “old process / wrong version” hallucinations.

### Non-goals (out)
- No browser extension yet.
- No ATS simulator yet.

---

## V1.4 — The Expedition (Operation Expedition Roadmap)

> Goal: build supply lines (Ops), evolve intelligence, and open the second front (Sidecar), **without** breaking local-first / privacy / governance.

### Tier 1 — Supply Lines (Ops)
1) **Release Automaton (GitHub Actions)**
- Merge → (explicit Release gate) → tag → release → build/push Docker (GHCR)
- Human gate preserved: no auto-merge; only runs on `Release vX.Y.Z` or manual dispatch.

2) **Fortification (Dependency freeze + audit)**
- Add `pip-audit` and `npm audit` into CI.
- Keep lockfiles stable; fail CI on high severity by default (tunable).

### Tier 2 — Intelligence Upgrade
3) **Gap Engine V1: Semantic Mapping**
- Add a lightweight local synonyms dictionary (e.g., Golang ↔ Go, k8s ↔ Kubernetes).
- No embeddings/vector DB required.

4) **Diplomat V2: Evidence Enforcement**
- Letters/emails must reference resume evidence; no empty claims.
- Use Application matches/suggestions as the allowed citation source.

5) **Project Picker**
- Score master projects/experience vs JD gaps and recommend top 3.

### Tier 3 — Sidecar (V1.4)
6) **Chrome Extension kernel (Manifest V3)**
- One-click ping localhost backend; validate CORS.

7) **HUD injection**
- Inject a minimal side panel to show gaps/matches.

8) **Instant Capture + Bind**
- In-page action triggers `/api/jd/capture` + `/api/applications/create`.

### Tier 4 — Polish
9) **Mission Control UX micro-refactor**
- Hover gap → highlight suggested section on resume side (no complex kanban).

10) **Field Manual (offline docs center)**
- Render README/docs in-app for quick reference.
