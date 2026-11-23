# Traceability Matrix: MoneyLens (T042)

| Requirement | Implementation | Deterministic tests | Evaluation cases / checks |
|-------------|----------------|---------------------|---------------------------|
| FR-001 batch 1–50, ≤ 1000 chars, order | `ai/parser.py::parse_batch`, `api/app.py` M1 | `test_parser.py` (INV-9, too long), `test_api.py::test_m1_invalid_batch` | P26, P27 (INV-9) |
| FR-002 / GR-1 masking | `core/masking.py` | `test_masking.py`, `test_masking_properties.py`, `test_parser.py::test_gr1_*`, `test_api.py::test_otp_never_stored_raw` | P01, P05, P07, P08, P16, P23, P27 (INV-6 on outputs **and prompts sent**) |
| FR-003 / INV-1 / INV-2 schema | `core/contracts.py`, JSON Schemas | `test_parser.py` (schema violation) | Layer 1 on every case |
| FR-004 transaction fields | prompt `parse_sms.v1`, `ai/parser.py` | `test_parser.py::test_us1_1_*` | P01–P05, P14–P21, P23, P24 (Layer 3) |
| FR-005 bill reminder | prompt, parser | `test_grounding.py::test_bill_*` | P06 |
| FR-006 / PROP-2 / GR-2 phishing | prompt | — | P09, P10, P11 (PROP-2, guardrail) |
| FR-007 / INV-3..5 / GR-6 grounding | `core/grounding.py`, `core/amounts.py` | `test_grounding.py`, `test_parser.py::test_gr6_*` | all parse cases (INV-3/4/5), P14 (AMOUNT_EXACT), P22 |
| INV-7 dates | `core/grounding.py` | `test_grounding.py::test_inv7_*` | P19, P20, P21 |
| PROP-1 OTP ≠ transaction | prompt | — | P07, P08, P27 |
| PROP-3 / GR-3 injection | prompt security rules | — | P13, P14, A09 |
| PROP-4 direction | prompt | — | all transaction cases |
| FR-008 duplicates | `storage/repository.py::save_result` | `test_api.py::test_fr008_duplicate_detected` | — |
| FR-009 model metadata | `ai/parser.py::_meta`, `ai/qa.py` | `test_parser.py::test_us1_1_*` | `eval-results.json.model` |
| FR-010 dashboard | `core/dashboard.py`, M2 | `test_query_dashboard.py::test_us3_1_*`, `test_api.py::test_m2_*` | — |
| FR-011 / INV-8 / SC-005 Q&A | `ai/qa.py`, `core/query_exec.py`, prompt `query.v1` | `test_qa.py`, `test_query_dashboard.py` | A01–A11 (independent recomputation in `checks/properties.py`) |
| FR-012 periods | prompt `query.v1`, `core/dates.py` | `test_amounts_dates.py` | A01, A03, A04, A06, A10, A11 |
| FR-013 / PROP-5 / GR-5 scope | prompt, `ai/qa.py` | `test_qa.py::test_prop5_*` | A07, A08, A09 |
| FR-015..017 / PROP-6 / GR-4 SplitEase | `splitease_client.py`, M5–M7 | `test_api.py` US5 tests (MockTransport) | — (deterministic) |
| FR-018 API + UI | `api/app.py`, `frontend/src` | `test_api.py`, `frontend/tests/*` | — |
| FR-019 dataset | `evals/dataset.json` (38 cases) | `tests/harness/test_checks.py` | — |
| FR-020 harness | `.harness/evaluate.py`, `.harness/checks/*` | `tests/harness/test_checks.py` | every run |
| SC-002 / SC-003 | — | — | guardrail cases, INV-6, PROP-1/2 |
| SC-004 20 messages < 60 s | parser concurrency (4) | — | `sc004_timing` in `eval-results.json` |
| SC-006 usability | UI | — | manual (student) |
