# Quickstart & Validation: SplitEase

## Prerequisites
Python ≥ 3.12, Node ≥ 20, from `Part-1A/`.

## Setup
```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"     # Windows; use .venv/bin/python elsewhere
cd frontend && npm ci && npm run build && cd ..
```

## Run the app
```bash
.venv/Scripts/python -m splitease        # http://127.0.0.1:8000
```

## Run the harness (all gates)
```bash
.venv/Scripts/python .harness/run_harness.py --label <run-name>
```
Expected: every gate `PASS`, overall `PASS`, evidence written to `evidence/harness-runs/`.

## End-to-end validation scenarios
1. Create group "Flat 4B" [Asha, Bilal, Chen] → balances all 0 (US1-1).
2. Asha pays ₹1000.00 EQUAL for all → balances +666.66 / −333.33 / −333.33 (US1-2).
3. Settle up shows `Bilal → Asha ₹333.33`, `Chen → Asha ₹333.33` (US3-1).
4. Record Bilal → Asha ₹333.33 → Bilal 0 (US4-1).
5. Enter amount `12.345` in the form → inline error, nothing sent (FR-022).
6. Export CSV → header row matches contracts/api.md (US6-1).

Each scenario has an automated counterpart in `tests/contract/` or `frontend/tests/`.
