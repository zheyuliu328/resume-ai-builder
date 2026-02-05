# Strategy

## Purpose
Build a **local-first** resume/JD toolkit that reliably improves application outcomes (targeted resume variants, evidence-backed writing, and a tight iteration loop).

## Core principles
- **Local-first / privacy-first**: user data stays on disk by default.
- **Outcome-driven**: features must directly support better targeting and faster iteration.
- **Governance, but minimal**: add only the controls that prevent real regressions.
- **No feature creep**: every new surface area must pay its rent.

## Milestones (high level)

### V1.0 — JD Killer
- Structured resume data
- Basic export pipeline

### V1.1–V1.2 — Safety & Expansion
- Rollback/snapshots
- Additional generators (cover letter, portfolio)

### V1.3 — Mission Control
- Application objects (JD ↔ variant)
- Gap analysis loop and UI for fast closure

### V1.4 — Ops Expedition
- Release automation
- Dependency locks
- Security audit workflow

## Operating model
- **Strategy lives here.**
- **Execution lives in** `OPERATIONS.md` (SOP, gates, exact commands).
