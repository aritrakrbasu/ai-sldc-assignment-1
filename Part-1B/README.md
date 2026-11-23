# Part 1B — MoneyLens (non-deterministic AI application)

MoneyLens is a personal finance inbox for Indian bank, card and UPI SMS. Paste a batch of
messages and Gemini classifies each one: transaction, OTP, promotion, bill reminder, suspected
phishing or other. For transactions it extracts amount, direction, merchant, account suffix,
date, channel and category. The dashboard shows where your money went. Plain-English questions
("How much did I spend on food last week?") become a structured query, and the app computes
the figures itself. A debit can be sent to a **SplitEase** group (Part 1A) after an explicit
confirmation.

Guardrails:
- OTPs and long card/account numbers are masked **before** anything is sent to the model.
- Phishing is flagged with reasons.
- Instructions embedded in SMS are ignored.
- Every amount, account suffix and merchant must appear in the SMS text, or the result is
  rejected or nulled.
- The model never does arithmetic.

## Layout

| Path | What |
|------|------|
| `.specify/memory/constitution.md` | Constitution v1.0.0 |
| `specs/001-sms-finance-inbox/` | `spec.md` (schema contract, INV/PROP/GR, threshold, clarifications), `plan.md`, `research.md`, `data-model.md`, `contracts/` (API + 4 JSON Schemas), `quickstart.md`, `tasks.md`, `traceability.md` |
| `src/moneylens/core/` | Pure core: masking, amounts, dates, grounding post-validator, contracts, query executor, dashboard |
| `src/moneylens/ai/` | Gemini client (+ FakeLLM for tests), parse pipeline, Q&A pipeline |
| `prompts/` | Versioned system prompts (`parse_sms.v1.md`, `query.v1.md`) |
| `evals/` | `dataset.json` (38 cases), `fixtures/transactions.json`, `threshold.json`, `build_dataset.py` |
| `.harness/evaluate.py` + `.harness/checks/` | **Single AI evaluation pipeline** (structural → property/invariant → semantic → threshold) |
| `.harness/run_harness.py` | Deterministic gates (Ruff, ESLint, tsc, Bandit, npm audit, pytest, Vitest). No model calls. |
| `evidence/` | SDD command log, initial/final generation, harness and eval runs, `eval-results.json`, `harness-log.md` |

## Setup

Requires Python ≥ 3.12 and Node ≥ 20. Run from `Part-1B/` (on macOS/Linux use
`.venv/bin/python`).

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
cp .env.example .env          # then set GEMINI_API_KEY=... (this file is git-ignored)
.venv/Scripts/python scripts/select_model.py   # picks the newest stable Gemini flash model
cd frontend && npm ci && npm run build && cd ..
```

## Run

```bash
.venv/Scripts/python -m moneylens     # http://127.0.0.1:8100
```

For "Split in SplitEase", also run Part 1A (`python -m splitease`, port 8000), or set
`SPLITEASE_URL`.

## Deterministic harness (no API key needed)

```bash
.venv/Scripts/python .harness/run_harness.py --label my-run
```

## AI evaluation harness (uses your key; about 140 model calls)

```bash
.venv/Scripts/python .harness/evaluate.py --label my-eval
```

- Each of the 38 cases runs **3 times**, and a case passes only if all 3 repeats pass.
- **Layer 1**: JSON Schema (`parse_result` / `query_result`).
- **Layer 2**: invariants and properties (grounding, no secret leakage, OTP ≠ transaction,
  phishing has reasons, injection-resistant kind, direction, date ranges, independent
  recomputation of every Q&A figure).
- **Layer 3**: weighted semantic score against ground truth.
- **Decision** (threshold declared in the spec before evaluation): 100% structural, 100% of
  guardrail cases, ≥ 95% of cases pass, and mean semantic score ≥ 0.90.
- Service failures (quota, network) are counted separately. More than 10% makes the run
  INCONCLUSIVE.
- `MONEYLENS_RPM` (default 10) limits requests per minute to stay inside free-tier quotas.
- `--cases P01,A03 --repeats 1` runs a quick SMOKE check, which can never count as the final
  PASS.

Evidence goes to `evidence/eval-runs/<timestamp>_<label>/` (`eval-results.json`, `failures.md`).
The dataset, threshold and checks are hash-locked (`.harness/eval.lock`). Changing them
requires `--relock --reason`, which is logged in `.harness/relock-log.md`.
