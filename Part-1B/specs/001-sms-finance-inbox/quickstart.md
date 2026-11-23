# Quickstart & Validation: MoneyLens

## Prerequisites
Python ≥ 3.12, Node ≥ 20 and a Gemini API key. Run from `Part-1B/`.

## Setup
```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
cp .env.example .env            # then put your key in GEMINI_API_KEY=
.venv/Scripts/python scripts/select_model.py   # writes MONEYLENS_MODEL to .env (R1)
cd frontend && npm ci && npm run build && cd ..
```

## Run
```bash
.venv/Scripts/python -m moneylens        # http://127.0.0.1:8100
```
For the SplitEase integration, also run Part 1A (`python -m splitease`, port 8000).

## Deterministic harness (no API calls)
```bash
.venv/Scripts/python .harness/run_harness.py --label <name>
```

## AI evaluation harness (real model, R = 3)
```bash
.venv/Scripts/python .harness/evaluate.py --label <name>
```
Expected: Layer-1/2/3 summary, aggregate PASS/FAIL/INCONCLUSIVE against
`evals/threshold.json`, evidence in `evidence/eval-runs/<ts>_<name>/`.

## Manual scenarios
1. Paste the SMS from spec US1-1..3 → TRANSACTION (₹250.00 FOOD), OTP (masked), PHISHING (red).
2. Dashboard for this month shows the debit under FOOD.
3. Ask "How much did I spend on food this month?" → computed total with the filters shown.
4. With Part 1A running: split the debit → preview → Confirm → the expense appears in SplitEase.
