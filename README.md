# Assignment 1 — Spec-Driven Development & Harness Engineering

**Course:** AI-Augmented Software Development Life Cycle (SE ZG534), BITS Pilani
**Student:** Aritra Basu

Both parts were built with the **GitHub Spec Kit** workflow:
constitution → specify → clarify → plan → tasks → analyze → implement. A **Claude Code** coding
agent implemented them. The process was then: harness validation → structured feedback →
repair → re-validation → human decision.

| Part | Application | Type | Folder |
|------|-------------|------|--------|
| 1A | **SplitEase**: split shared expenses with friends and flatmates to the exact paisa (FastAPI + React) | Deterministic | [`Part-1A/`](Part-1A/README.md) |
| 1B | **MoneyLens**: AI finance inbox that turns bank/UPI SMS into transactions, flags phishing, answers spending questions and sends a bill to SplitEase (Gemini + FastAPI + React) | Non-deterministic | [`Part-1B/`](Part-1B/README.md) |

## Where to look

| Evidence | Part 1A | Part 1B |
|----------|---------|---------|
| Constitution | `Part-1A/.specify/memory/constitution.md` | `Part-1B/.specify/memory/constitution.md` |
| Spec (+ clarifications), plan, tasks, analysis fixes | `Part-1A/specs/001-shared-expense-splitter/` | `Part-1B/specs/001-sms-finance-inbox/` |
| Exact Spec Kit command inputs | `Part-1A/evidence/sdd-prompts.md` | `Part-1B/evidence/sdd-prompts.md` |
| Traceability matrix | `.../traceability.md` | `.../traceability.md` |
| Harness | `Part-1A/.harness/` | `Part-1B/.harness/` (`evaluate.py` + `run_harness.py`) |
| Evaluation dataset | — | `Part-1B/evals/dataset.json` (38 cases) |
| First generation / accepted generation | `Part-1A/evidence/{initial,final}-generation/` | `Part-1B/evidence/{initial,final}-generation/` |
| Every harness run (raw logs, JSON, feedback) | `Part-1A/evidence/harness-runs/` | `Part-1B/evidence/harness-runs/`, `Part-1B/evidence/eval-runs/` |
| Harness log + human decision | `Part-1A/evidence/harness-log.md` | `Part-1B/evidence/harness-log.md` |

The git history follows the SDD order: each Spec Kit step, then tests (and for 1B, the evaluation
dataset and harness) **before** implementation, then harness-driven repairs.

## Quick start

See each part's README. In short:

```bash
# Part 1A
cd Part-1A && python -m venv .venv && .venv/Scripts/python -m pip install -e ".[dev]"
cd frontend && npm ci && npm run build && cd ..
.venv/Scripts/python -m splitease                       # http://127.0.0.1:8000
.venv/Scripts/python .harness/run_harness.py --label check

# Part 1B (needs a Gemini API key in Part-1B/.env, never committed)
cd Part-1B && python -m venv .venv && .venv/Scripts/python -m pip install -e ".[dev]"
cp .env.example .env && .venv/Scripts/python scripts/select_model.py
cd frontend && npm ci && npm run build && cd ..
.venv/Scripts/python -m moneylens                       # http://127.0.0.1:8100
.venv/Scripts/python .harness/run_harness.py --label check
.venv/Scripts/python .harness/evaluate.py --label eval
```

No API keys, credentials or `.env` files are committed (see `.gitignore`).
