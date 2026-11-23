# SplitEase Constitution

## Core Principles

### I. Exact Money Arithmetic (NON-NEGOTIABLE)
- All monetary amounts MUST be stored, computed and transmitted as integer minor units
  (paise, 1 INR = 100 paise). Floating-point types MUST NOT be used for money anywhere in
  the domain core, API, persistence or tests.
- Every split MUST be exact: the sum of all member shares of an expense MUST equal the
  expense total, to the paisa.
- Any rounding remainder MUST be distributed by one documented, deterministic rule so that
  identical inputs always produce identical shares.
- The sum of all member net balances in a group MUST equal exactly 0 at all times.

Rationale: shared-expense apps lose user trust the moment one rupee "disappears". Integer
paise and a single remainder rule make every result reproducible and binary-testable.

### II. Deterministic, Pure Domain Core
- Business rules (splitting, balances, settlement plan) MUST live in a pure Python package
  with no I/O, no clock reads and no randomness.
- The same inputs MUST always produce byte-identical outputs, including ordering of lists
  (ties broken by a documented stable key).
- The API and UI layers MUST NOT re-implement business rules; they call the core.

Rationale: a pure core can be exhaustively unit-tested and its behaviour cannot drift
between the API and the UI.

### III. Specification-Derived Tests (NON-NEGOTIABLE)
- Every functional requirement and acceptance scenario in the approved spec MUST map to at
  least one automated test whose name or docstring cites the requirement ID (e.g. `FR-007`).
- Tests MUST assert exact values (exact paise, exact HTTP status codes, exact error codes),
  never "approximately" or "non-empty".
- Tests MUST NOT be deleted, skipped, marked xfail or have assertions weakened to obtain a
  passing harness. A requirement change MUST go through the spec first.

Rationale: the harness is only as strong as its assertions; binary tests make the
accept/reject decision objective.

### IV. Harness-Gated Delivery
- No implementation is accepted unless the local harness (`.harness/run_harness.py`)
  reports PASS on all mandatory gates: Lint (Ruff + ESLint), Security (Bandit +
  `npm audit --audit-level=high`), and Tests (pytest + frontend tests).
- Domain-core line coverage MUST be >= 90%.
- Harness configuration MUST NOT be weakened (rules disabled, thresholds lowered, paths
  excluded) to make a failing run pass. Every harness run MUST be recorded under
  `evidence/` with its raw stdout/stderr and exit code.
- Failures MUST be fed back to the coding agent as structured evidence (gate, failing
  test/rule, expected vs observed) and fixed in code, then the same gates re-run.

Rationale: AI-generated code is not correct because it runs; independent gates decide.

### V. Simple, Safe API & UI
- The REST API MUST validate all input and reject invalid requests with HTTP 422 (schema
  errors) or 400/404/409 (domain errors) and a machine-readable `error.code`.
- No secrets MUST be committed; the app MUST NOT require any secret to run.
- User-supplied text MUST be rendered as text in the UI (no `dangerouslySetInnerHTML`).
- CSV export MUST neutralise spreadsheet formula injection (cells starting with `=`, `+`,
  `-`, `@` are prefixed with `'`).
- YAGNI: no authentication, multi-currency or cloud deployment in this version.

Rationale: a small, well-validated surface is easier to secure and to test.

## Technology & Performance Constraints

- Backend: Python 3.12+ (developed on 3.15), FastAPI, Pydantic v2, SQLite via the standard
  library `sqlite3` module (parameterised queries only).
- Frontend: React + TypeScript built with Vite; ESLint for linting; Vitest for tests.
- Limits: a group holds 2–50 members; an expense amount is 1 to 1,000,000,000 paise
  (₹0.01 to ₹1 crore); description length 1–120 characters.
- Settle-up for a group of 50 members MUST compute in under 100 ms on a developer laptop.
- One command per part MUST start the app and one command MUST run the full harness.

## Development Workflow & Quality Gates

- Flow: constitution → specify → clarify → plan → tasks → analyze → implement → harness →
  feedback/repair → re-run → human ACCEPT/REJECT.
- The first AI-generated implementation MUST be preserved in `evidence/initial-generation/`
  before any harness-driven correction; the accepted version in
  `evidence/final-generation/`.
- Ambiguities found after implementation starts MUST be resolved by amending the spec
  (with a dated note in its Clarifications section), never silently in code.
- The final ACCEPT/REJECT decision is made and recorded by the human student, not by the
  coding agent.

## Governance

- This constitution supersedes other practices for SplitEase. Every plan MUST include a
  Constitution Check against Principles I–V.
- Amendments require a version bump (semantic versioning), an updated Last Amended date and
  a note in the commit message.
- Any deviation MUST be justified in the plan's Complexity Tracking table.

**Version**: 1.0.0 | **Ratified**: 2026-11-23 | **Last Amended**: 2026-11-23
