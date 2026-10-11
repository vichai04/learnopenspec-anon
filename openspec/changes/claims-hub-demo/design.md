## Context

The project root holds `claims_hub.sqlite` (SQLite 3, synthetic data for 4 hospitals and 5 payers), `README.md` (schema and column meanings), and `PRD.md` (the target platform). The repository is not a git repository and has no application code yet. See proposal.md - Why for motivation and specs/ for the behavior each screen must provide.

The source data is deliberately inconsistent: `hospitals.date_format` differs per hospital (`YYYYMMDD`, `DD/MM/YYYY`, `YYYY-MM-DD`, all in พ.ศ.), and visit dates in the sample include 2-digit Buddhist years (for example `69-08-01`). Payer codes and sex codes are hospital-local and resolved through mapping tables.

## Goals / Non-Goals

**Goals:**
- Run locally with one command and open in a browser.
- Read `claims_hub.sqlite` without modifying it.
- Keep the normalization, validation, and rule-resolution logic in plain functions that can be tested without the web layer.
- Keep payer-specific behavior in data (`payer_rules`), never in code.

**Non-Goals:**
- Writing to the database, submitting claims, or any network call to a payer or HIS.
- Authentication, multi-user access, or deployment.
- Performance tuning beyond measuring validation time per claim.
- Parsing HL7 v2, XML, or JSON payloads. The demo reads already-extracted tables only.

## Decisions

**Reflex (Python) for the whole web application: UI, state, and event handlers in one Python codebase.**
- The user chose Reflex, so pages are Reflex components and each view's data lives in a Reflex `State` class. Event handlers call the core functions directly; there is no separate JSON API layer.
- Reflex compiles a React frontend and runs a FastAPI backend, so no hand-written JavaScript is needed. Version is pinned in `requirements.txt` at implementation time (PyPI latest at proposal time: 0.10.0).
- Alternative considered: FastAPI with a static HTML/JavaScript frontend. Superseded by the Reflex choice; it would have needed two languages and a hand-built UI.

**Theme: custom Tailwind integration, dark modern dashboard.**
- Styling uses Tailwind utility classes through Reflex's `class_name` prop, with a custom Tailwind theme that defines the dashboard tokens: a dark slate background, two or three surface levels for cards, one accent color for interactive elements and selected filters, and semantic colors for status (approved, partial, rejected, pended).
- The tokens live in one place (the Tailwind theme config and `demo/claims_hub_demo/theme.py`), so colors and spacing change without touching pages.
- Dashboard conventions: metric tiles with large numbers, thin borders instead of heavy shadows, rounded cards, a left sidebar for navigation, and compact tables with sticky headers.
- Shared components (status tag, metric tile, data table, notice banner) use only these tokens, so the look stays consistent across pages.
- Whether Reflex's bundled Tailwind setup accepts a custom theme config is checked in task 1.1 before the theme is built. If it does not, the same tokens are applied as Tailwind classes on the shared components.

**Read-only connection.** The database is opened with `file:claims_hub.sqlite?mode=ro` in URI form, so writes fail at the driver level and the non-modification requirement is enforced, not only promised. The connection helper is plain Python using the standard-library `sqlite3` module, called from the Reflex state at startup and on each query.

**Pure-function core.** Normalization, rule selection, and validation live in modules with no Reflex or SQL-string dependencies. Each takes plain records and the reference data as input and returns results. The Reflex state only loads data and calls these functions. This keeps validation timing measurable and the logic testable without running the web app.

**Date parsing by declared format, with 2-digit year fallback.** Each hospital's `date_format` selects a parser. Two-digit Buddhist years are read as 2500 + YY, matching the sample data. A value that fails its declared parser is reported as an error rather than guessed, per the normalization spec.

**Rule evaluation as a table of rule-type handlers.** Each catalogued `rule_type` maps to one handler function. Unknown types produce an "unrecognized" result. A new payer adds rows, not handlers, unless it introduces a new rule type, which is the same extension point the PRD asks for.

**Reference-table checks use the database's own tables.** `ref_icd10`, `ref_icd9cm`, `ref_drug`, and `ref_service_item` are loaded once at startup into memory. This keeps validation of a claim independent of database round-trips, which keeps the timing result about the logic.

**Thai and English labels in one dictionary.** All UI strings come from one dictionary module keyed by language, so the labels can be checked in one place and a language toggle is a state variable, not a rewrite.

## Risks / Trade-offs

- **Synthetic rules are not real payer rules** → Every screen that shows a rule carries the note from the README that the rules are simplified for teaching. The rule data is kept in the database, so it can be edited without code changes.
- **Ambiguous date formats** (for example `01/08/69` could be read several ways) → The parser uses only the hospital's declared format. Values that do not match are reported, not guessed.
- **Validation timing on a laptop does not show production latency** → The demo reports the measured time and states the hardware context. It does not claim the PRD's latency target is met.
- **In-memory reference tables grow with the database** → The sample tables are small (tens of rows). A larger dataset would need lazy loading; this is out of scope for the demo.
- **Reflex is a newer framework with a compile step** → Pin the version in `requirements.txt`. The first task verifies a minimal Reflex app builds and runs on this machine before any demo code is written.
- **Reference tables are cached at startup** → The app reads the database file once at startup and does not re-read it. Replacing the file requires restarting the app.

## Migration Plan

Not applicable. The demo is new, runs from the project root, and changes no existing files. Removing the demo means deleting its directory.

## Open Questions

None that change the specs or task breakdown. The stack choice above can be changed before implementation if you prefer a different one.
