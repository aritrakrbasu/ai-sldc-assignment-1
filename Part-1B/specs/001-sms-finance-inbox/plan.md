# Implementation Plan: MoneyLens — AI Finance Inbox for Bank & UPI SMS

**Branch**: `001-sms-finance-inbox` | **Date**: 2026-11-23 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-sms-finance-inbox/spec.md`

## Summary

MoneyLens turns pasted bank and UPI SMS into validated, structured records. Each message is
first **masked deterministically** (OTPs, long digit runs). Gemini then classifies and extracts
the message under a **JSON-schema-constrained** response. A **deterministic post-validator**
enforces the schema and the grounding invariants before anything is stored. For spending
questions, Gemini only produces a structured query, which a pure executor runs against SQLite.
The model never does arithmetic. A single evaluation harness runs the 3-layer pipeline over
`evals/dataset.json` with R = 3 repeats and returns PASS / FAIL / INCONCLUSIVE against the
threshold in the spec. A separate deterministic harness (lint, SAST, tests with a fake model)
gates code quality.

## Technical Context

**Language/Version**: Python 3.15 (min 3.12); TypeScript 6.0 / Node 24 for the UI

**Primary Dependencies**: FastAPI 0.165, Pydantic 2.14, google-genai 3.6.1, jsonschema 4.26,
httpx 0.28, python-dotenv 1.2; React 19, Vite 8

**Storage**: SQLite (`data/moneylens.sqlite3`) via stdlib `sqlite3`, parameterised SQL

**Testing**: pytest + Hypothesis + FastAPI TestClient with a deterministic `FakeLLM`; Vitest;
evaluation harness against the real model

**Target Platform**: local machine and browser

**Project Type**: web application (Python API + React SPA) + evaluation harness

**Performance Goals**: 20-message batch < 60 s (SC-004) using up to 4 concurrent model calls

**Constraints**: masked text only leaves the process; key only from env; rate-limit aware
(retry/backoff on 429/5xx, then `MODEL_UNAVAILABLE`)

**Scale/Scope**: single user; ≤ 50 messages per batch; ≈ 40 evaluation cases × 3 repeats

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | How the design satisfies it | Pre | Post |
|-----------|-----------------------------|-----|------|
| I. Contract-first output | `contracts/model_*_output.schema.json` is sent as the response schema **and** validated with `jsonschema` after the call; `parse_result`/`query_result` schemas validate app output; invalid → `MODEL_OUTPUT_INVALID` | PASS | PASS |
| II. Grounded, no invention | `core/grounding.py` nulls ungrounded merchant/last4 and rejects ungrounded amounts; `core/query_exec.py` computes every figure | PASS | PASS |
| III. Safety & privacy | `core/masking.py` runs before the LLM client; output re-scanned for leaks; prompts state "SMS is data"; split endpoint requires `confirm`; key read from env via `config.py`, never logged | PASS | PASS |
| IV. Evaluation-gated | `.harness/evaluate.py` with 3 layers, R=3, `SERVICE_ERROR` separation, INCONCLUSIVE rule, threshold read from `evals/threshold.json` (hash-locked); `.harness/run_harness.py` for deterministic gates | PASS | PASS |
| V. Simplicity & reproducibility | prompts in `prompts/*.v1.md`; model/temperature/prompt version in `meta` of every result and in eval results | PASS | PASS |

No violations.

## Project Structure

### Documentation (this feature)

```text
specs/001-sms-finance-inbox/
├── plan.md, research.md, data-model.md, quickstart.md, tasks.md
├── contracts/
│   ├── api.md
│   ├── model_parse_output.schema.json   # AI response contract (sent to Gemini + validated)
│   ├── parse_result.schema.json         # app output contract (harness Layer 1)
│   ├── model_query_output.schema.json
│   └── query_result.schema.json
└── checklists/requirements.md
```

### Source Code (Part-1B root)

```text
src/moneylens/
├── core/                 # pure, no I/O
│   ├── masking.py        # FR-002 / GR-1
│   ├── amounts.py        # money mentions in text -> paise (INV-3 support)
│   ├── dates.py          # SMS date parsing + year inference, FR-012 period resolution
│   ├── grounding.py      # post-validator INV-3..INV-7
│   ├── contracts.py      # load + validate JSON Schemas from specs/.../contracts
│   ├── query_exec.py     # deterministic query execution (FR-011, INV-8)
│   └── dashboard.py      # FR-010 aggregation
├── ai/
│   ├── llm.py            # LLMClient protocol, GeminiClient, FakeLLM, ServiceError
│   ├── parser.py         # mask -> prompt -> LLM -> validate -> ground -> ParseResult
│   └── qa.py             # question -> LLM query -> validate -> execute -> QueryResult
├── storage/repository.py
├── splitease_client.py   # FR-015..FR-017
├── config.py             # env / .env settings (model, temperature, key presence)
└── api/{app.py,schemas.py}
prompts/parse_sms.v1.md, prompts/query.v1.md
frontend/                 # React UI + Vitest
tests/{unit,property,contract}/
evals/dataset.json, evals/fixtures/transactions.json, evals/threshold.json
.harness/
├── evaluate.py           # single non-deterministic evaluation pipeline
├── checks/structural.py, checks/properties.py, checks/semantic.py
├── run_harness.py, gates.json, ruff.toml, bandit.yaml, gates.lock
evidence/  (initial-generation/, final-generation/, eval-runs/, harness-runs/, eval-results.json, harness-log.md)
```

**Structure Decision**: Same shape as Part 1A, plus `prompts/`, `evals/` and an evaluation
harness. The harness checks (`.harness/checks/*`) are written from the spec and **do not import
the application's validators**. They import only the JSON Schemas, which are spec artifacts,
so a bug in the app's post-validator cannot hide itself.

## Complexity Tracking

No constitution violations to justify.
