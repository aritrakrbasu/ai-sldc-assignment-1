# Implementation Plan: SplitEase — Shared Expense Splitter

**Branch**: `001-shared-expense-splitter` | **Date**: 2026-11-23 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-shared-expense-splitter/spec.md`

## Summary

SplitEase records shared expenses for a group, splits each expense exactly in integer paise
(EQUAL / EXACT / PERCENT / SHARES), derives net balances that always sum to zero, proposes a
deterministic greedy settle-up plan, records immutable settlements and exports a CSV ledger.
Approach: a pure, I/O-free Python domain core (`splitease.core`) holds every business rule; a
thin FastAPI layer validates input, persists to SQLite and calls the core; a React + TypeScript
single-page UI (built by Vite) is served by the same FastAPI process so one command runs the app.

## Technical Context

**Language/Version**: Python 3.15 (backend, min 3.12); TypeScript 7 / Node 24 (frontend build only)

**Primary Dependencies**: FastAPI 0.165, Pydantic 2.14, Uvicorn 0.54; React 19, Vite 8

**Storage**: SQLite file via stdlib `sqlite3`, parameterised queries only (`data/splitease.sqlite3`)

**Testing**: pytest 9 + pytest-cov + Hypothesis (property tests), FastAPI `TestClient` (contract
tests), Vitest 5 + Testing Library + jsdom (frontend unit tests)

**Target Platform**: Local machine (Windows/macOS/Linux), modern evergreen browser

**Project Type**: Web application (Python API + React SPA)

**Performance Goals**: settle-up for 50 members < 100 ms (constitution); page interactions < 1 s

**Constraints**: no floats for money anywhere; deterministic outputs; no secrets required

**Scale/Scope**: 2–50 members per group; tens of groups; hundreds of expenses per group

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Pre-design | Post-design |
|-----------|------|------------|-------------|
| I. Exact Money Arithmetic | Money is `int` paise in core, DB (`INTEGER`), API (JSON integers) and UI (`number` integers, parsed from strings without floats); remainder rules FR-004/FR-008 | PASS | PASS — see data-model.md, contracts/api.md, research R3 |
| II. Deterministic Pure Core | `splitease.core` imports nothing from api/storage, no clock/random; stable tie-break by member order | PASS | PASS — module layout below; enforced by test `test_core_is_pure` |
| III. Spec-Derived Tests | Every FR / acceptance scenario cited in a test name or docstring; traceability matrix in tasks.md | PASS | PASS — contract & unit test plan in quickstart.md |
| IV. Harness-Gated Delivery | `.harness/run_harness.py` gates: ruff, eslint, bandit, npm audit (high), pytest (+cov ≥ 90% core), vitest; JSON+log to evidence | PASS | PASS |
| V. Simple, Safe API & UI | 422 schema / 400/404/409 domain errors with `error.code`; no secrets; text rendering only; CSV formula neutralisation; no auth (YAGNI) | PASS | PASS |

No violations → Complexity Tracking empty.

## Project Structure

### Documentation (this feature)

```text
specs/001-shared-expense-splitter/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── api.md
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (Part-1A root)

```text
src/splitease/
├── core/                # PURE domain (Principle II) — no I/O
│   ├── errors.py        # DomainError + error codes
│   ├── money.py         # paise <-> rupee string helpers
│   ├── splitting.py     # EQUAL / EXACT / PERCENT / SHARES, largest-remainder
│   ├── balances.py      # net balances from expenses + settlements
│   ├── settle.py        # greedy settle-up plan
│   └── ledger_csv.py    # CSV export with formula neutralisation
├── storage/
│   └── repository.py    # sqlite3 repository (parameterised SQL)
├── api/
│   ├── schemas.py       # Pydantic request/response models
│   └── app.py           # FastAPI app, routes, error handlers, static SPA mount
└── __main__.py          # `python -m splitease` → uvicorn

frontend/
├── src/
│   ├── api.ts           # typed API client
│   ├── money.ts         # rupee string -> paise (FR-022), formatting
│   ├── App.tsx, components/*.tsx
│   └── main.tsx
└── tests/               # vitest

tests/
├── unit/                # core rules, one file per module
├── property/            # hypothesis invariants (SC-001, SC-004)
└── contract/            # HTTP API contract tests (status codes, error codes, payloads)

.harness/
├── run_harness.py       # orchestrator: runs all gates, writes evidence
├── ruff.toml, bandit.yaml
└── gates.json           # gate definitions (commands, thresholds)
```

**Structure Decision**: Single Part-1A project with `src/` (Python package, src-layout), `tests/`
(Python tests) and `frontend/` (SPA with its own tests). This satisfies the assignment's required
`src/`, `tests/`, `.harness/`, `evidence/` layout while keeping the frontend toolchain isolated.

## Complexity Tracking

No constitution violations to justify.
