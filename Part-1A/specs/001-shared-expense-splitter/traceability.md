# Traceability Matrix: SplitEase (T048)

Requirement → tasks → implementation → tests. Test names/docstrings cite the IDs (constitution III).

| Req | Tasks | Implementation | Tests |
|-----|-------|----------------|-------|
| FR-001 | T015, T018 | `core/groups.py` | `tests/unit/test_groups_validation.py`, `tests/contract/test_groups_api.py` |
| FR-002 | T016, T022 | `api/app.py` (C2, C3) | `tests/contract/test_groups_api.py` |
| FR-003 | T006, T017, T021 | `core/money.py`, `api/schemas.py` | `tests/unit/test_money.py`, `tests/contract/test_expenses_api.py` |
| FR-004 | T013, T019 | `core/splitting.py` (EQUAL) | `tests/unit/test_splitting_equal.py` |
| FR-005 | T023, T026 | `core/splitting.py` (EXACT) | `tests/unit/test_splitting_modes.py` |
| FR-006 | T006, T023, T026 | `core/money.py::parse_percent`, `core/splitting.py` | `tests/unit/test_money.py`, `tests/unit/test_splitting_modes.py` |
| FR-007 | T023, T026 | `core/splitting.py` (SHARES) | `tests/unit/test_splitting_modes.py` |
| FR-008 | T023, T026 | `core/splitting.py::_largest_remainder` | `tests/unit/test_splitting_modes.py` |
| FR-009 | T013, T024 | `core/splitting.py` | `tests/property/test_split_invariants.py` (600 examples) |
| FR-010 | T013, T019 | `core/splitting.py::_ordered_participants` | `tests/unit/test_splitting_equal.py`, `tests/contract/test_expenses_api.py` |
| FR-011 | T037, T038 | `api/app.py` (C5), `storage/repository.py::delete_expense` | `tests/contract/test_settle_settlement_delete_export_api.py` (US5) |
| FR-012 | T014, T020 | `core/balances.py` | `tests/unit/test_balances.py` |
| FR-013 | T014, T024 | `core/balances.py` | `tests/unit/test_balances.py`, `tests/property/test_split_invariants.py` (500 op sequences) |
| FR-014 | T028, T029, T031 | `core/settle.py` | `tests/unit/test_settle.py`, `tests/property/test_settle_invariants.py` |
| FR-015 | T033, T034, T035 | `core/settlements.py`, `core/balances.py`, `api/app.py` (C6 + 405) | `tests/unit/test_settlements.py`, `tests/unit/test_balances.py`, contract US4 tests |
| FR-016 | T039, T041 | `core/ledger_csv.py` | `tests/unit/test_ledger_csv.py`, contract C9 test |
| FR-017 | T039, T041 | `core/ledger_csv.py::_safe` | `tests/unit/test_ledger_csv.py`, contract C9 test |
| FR-018 | T011, T025 | `api/app.py` error handlers, `storage/repository.py::_tx` | contract tests "nothing saved" assertions |
| FR-019 | T010 | `storage/repository.py` | `tests/contract/test_groups_api.py::test_fr019_*` |
| FR-020 | T044, T045 | `frontend/src/*` | `frontend/tests/money.test.ts`, `frontend/tests/App.test.tsx` |
| FR-021 | T024, T029, T039 | pure core | property determinism tests, `test_sc006_*` |
| FR-022 | T042, T044 | `frontend/src/money.ts::parseRupees` | `frontend/tests/money.test.ts`, `frontend/tests/App.test.tsx` |
| SC-001 | T024 | — | `tests/property/test_split_invariants.py` |
| SC-002 | T050 | — | manual (quickstart.md) |
| SC-003 | T028 | `core/settle.py` | `tests/unit/test_settle.py::test_constitution_perf_50_members_under_100ms` |
| SC-004 | T029 | `core/settle.py` | `tests/property/test_settle_invariants.py` |
| SC-005 | T023, T025 | core error codes | `tests/unit/test_splitting_*.py`, `tests/contract/test_expenses_api.py` |
| SC-006 | T039, T040 | `core/ledger_csv.py` | `tests/unit/test_ledger_csv.py`, contract `test_sc006_*` |
