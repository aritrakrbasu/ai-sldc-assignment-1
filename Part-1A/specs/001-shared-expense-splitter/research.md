# Research: SplitEase

No `NEEDS CLARIFICATION` items remained in Technical Context. Each decision below was checked
against the local environment on 2026-11-23 (`pip install` into a Python 3.15.1 venv succeeded
for fastapi 0.165.0, pydantic 2.14.4, uvicorn 0.54.0, pytest 9.2.0, pytest-cov 7.1.0,
hypothesis 6.170.17, ruff 0.17.6, bandit 1.9.4; `npm view` reported react 19.3.1, vite 8.3.8,
typescript 7.0.2, vitest 5.1.1, eslint 10.15.0).

## R1. Backend framework
- **Decision**: FastAPI + Pydantic v2.
- **Rationale**: Declarative request validation gives automatic HTTP 422 for schema errors
  (constitution V); `TestClient` makes contract tests simple; serves the built SPA as static files.
- **Alternatives**: Flask (manual validation), Django (too heavy for scope).

## R2. Storage
- **Decision**: stdlib `sqlite3`, one file, parameterised queries; store split inputs and computed
  shares as rows. Balances are always recomputed from rows by the core (never stored).
- **Rationale**: Zero extra dependency, persists across restarts (FR-019), Bandit can verify no
  string-built SQL (B608).
- **Alternatives**: JSON file (no atomic writes), SQLAlchemy (unnecessary abstraction).

## R3. Exact money and percentages
- **Decision**: Money = `int` paise. Percentages travel as **basis points** (`int`, 100.00% =
  10000) inside the core and as strings with ≤ 2 decimals (e.g. `"33.33"`) in the API, parsed with
  `decimal.Decimal` → exact integer. Largest-remainder computed with integer arithmetic:
  `num = amount * weight`, `floor = num // total_weight`, `rem = num % total_weight`.
- **Rationale**: Avoids binary floating point entirely (constitution I); exact remainders compare
  as integers so ties are deterministic.
- **Alternatives**: `float` percentages (non-deterministic rounding), `Decimal` everywhere (works
  but integer math is simpler to reason about and test).

## R4. Settle-up algorithm
- **Decision**: Greedy: sort debtors by (|balance| desc, member order asc) and creditors likewise;
  repeatedly pay `min(|debt|, credit)` from the top debtor to the top creditor, re-sorting after
  each step. Produces ≤ k−1 payments.
- **Rationale**: Deterministic, O(k² log k) worst case — trivially < 100 ms for 50 members.
  The true minimum-transaction problem is NP-hard (spec Assumptions).
- **Alternatives**: subset-sum optimal search (exponential), pairwise debts (up to k² payments).

## R5. Frontend
- **Decision**: React 19 + TypeScript + Vite 8, plain CSS; `fetch` API client; ESLint
  (typescript-eslint, react-hooks); Vitest + Testing Library + jsdom.
- **Rationale**: The student explicitly chose React. React 19 is current (the plan input said
  React 18; 19 is backward compatible for this usage and avoids starting on an outdated major).
- **Alternatives**: Streamlit (no real API), Next.js (server runtime not needed).

## R6. Rupee input parsing in UI (FR-022)
- **Decision**: Regex `^\d{1,8}(\.\d{1,2})?$` on the trimmed string, then build paise from the
  integer and fraction parts as integers (`rupees*100 + fraction padded to 2 digits`).
- **Rationale**: Never uses `parseFloat`; `"0.1"` → 10 exactly; rejects `1e3`, `-5`, `12.345`.

## R7. Harness tooling
- **Decision**: Ruff (lint, rules E,F,W,I,B,UP,S,SIM), ESLint; Bandit (`-ll` medium+ severity
  fails), `npm audit --audit-level=high`; pytest with `--cov=splitease.core --cov-fail-under=90`;
  Vitest. Orchestrator `.harness/run_harness.py` runs each gate as a subprocess, captures
  stdout/stderr/exit code, writes `evidence/harness-runs/<timestamp>/` with `result.json` and
  raw logs, and exits non-zero if any mandatory gate fails.
- **Rationale**: Independent of the generated code, reproducible, produces structured feedback
  for the coding agent (constitution IV).

## R8. Error format
- **Decision**: All domain errors → `{"error": {"code": "SPLIT_SUM_MISMATCH", "message": "..."}}`
  with 400 (validation of domain rules), 404 (unknown group/expense), 409 reserved; Pydantic schema
  errors → 422 re-shaped as `{"error": {"code": "VALIDATION_ERROR", "message", "details"}}`.
