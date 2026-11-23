# Part 1A — SplitEase (deterministic application)

SplitEase is a web app for flatmates, friends and trip groups to record shared expenses and settle
up **to the exact paisa**. Expenses can be split equally, by exact amounts, by percentages or by
shares; balances always sum to zero; a greedy settle-up plan tells everyone who pays whom.

Built with the GitHub Spec Kit SDD flow and gated by an independent local harness.

## Layout

| Path | What |
|------|------|
| `.specify/memory/constitution.md` | Constitution v1.0.0 (measurable engineering constraints) |
| `specs/001-shared-expense-splitter/` | `spec.md` (+ clarifications), `plan.md`, `research.md`, `data-model.md`, `contracts/api.md`, `quickstart.md`, `tasks.md`, `traceability.md`, `checklists/` |
| `src/splitease/core/` | Pure, deterministic domain core (splitting, balances, settle-up, CSV) |
| `src/splitease/api/`, `src/splitease/storage/` | FastAPI layer and SQLite repository |
| `frontend/` | React 19 + TypeScript UI (Vite) and its Vitest tests |
| `tests/` | Spec-derived pytest suites: `unit/`, `property/` (Hypothesis), `contract/` (HTTP) |
| `.harness/` | Harness runner, gate definitions, lint/SAST config, config hash lock |
| `evidence/` | SDD command log, initial/final generation snapshots, every harness run, `harness-log.md` |

## Prerequisites

Python ≥ 3.12 and Node ≥ 20. Commands below are run from `Part-1A/`
(on macOS/Linux use `.venv/bin/python` instead of `.venv/Scripts/python`).

## Setup

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
cd frontend && npm ci && npm run build && cd ..
```

## Run the app

```bash
.venv/Scripts/python -m splitease
```

Open <http://127.0.0.1:8000>. Data is stored in `data/splitease.sqlite3` (override with the
`SPLITEASE_DB` environment variable). For UI development, run `npm run dev` in `frontend/` (it
proxies `/api` to port 8000).

## Run the harness

```bash
.venv/Scripts/python .harness/run_harness.py --label my-run
```

| Gate | Tool | Fails when |
|------|------|-----------|
| `lint-python` | Ruff (E,F,W,I,B,UP,S,SIM) | any finding |
| `lint-frontend` | ESLint (+ bans `dangerouslySetInnerHTML`, `parseFloat`) | any error/warning |
| `typecheck-frontend` | `tsc` strict | any type error |
| `security-python` | Bandit `-ll` | any medium/high issue |
| `security-deps` | `npm audit --audit-level=high` | any high/critical advisory |
| `tests-python` | pytest + coverage | any failure, or `splitease.core` coverage < 90 % |
| `tests-frontend` | Vitest | any failure |

Each run writes `evidence/harness-runs/<timestamp>_<label>/` containing `result.json`, one raw log
per gate, JUnit XML and `feedback.md` (the structured failure evidence given to the coding agent).
The harness configuration is hash-locked in `.harness/gates.lock`; any change makes the harness
refuse to run until it is re-locked with a reason, which is appended to `.harness/relock-log.md`.
