---
description: "Task list for SplitEase — Shared Expense Splitter"
---

# Tasks: SplitEase — Shared Expense Splitter

**Input**: Design documents from `/specs/001-shared-expense-splitter/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md, quickstart.md

**Tests**: REQUIRED — constitution Principle III (spec-derived tests with exact assertions).
Tests for each story are written from the spec **before** the implementation for that story and
must cite the FR / acceptance-scenario id they verify.

**Organization**: Grouped by user story; each story is independently testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallelizable (different files, no unmet dependencies)
- **[Story]**: US1 … US7 from spec.md

---

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Create Python package skeleton `src/splitease/{core,storage,api}/__init__.py`, `src/splitease/__main__.py` and `pyproject.toml` (src-layout, deps from plan.md, `[dev]` extra with pytest, pytest-cov, hypothesis, httpx, ruff, bandit)
- [X] T002 [P] Scaffold Vite React-TS app in `frontend/` (React 19, Vite 8, Vitest, Testing Library, jsdom, ESLint with typescript-eslint + react-hooks) with `npm run build|lint|test` scripts; dev proxy `/api` → `http://127.0.0.1:8000`
- [X] T003 [P] Harness config: `.harness/ruff.toml` (rules E,F,W,I,B,UP,S,SIM; tests may use `assert`), `.harness/bandit.yaml`, `.harness/gates.json` listing gates lint-python, lint-frontend, security-python, security-deps, tests-python (cov ≥ 90 on `splitease.core`), tests-frontend (research R7)
- [X] T004 Harness runner `.harness/run_harness.py`: runs each gate as subprocess, captures stdout/stderr/exit code/duration, writes `evidence/harness-runs/<UTC-timestamp>_<label>/{result.json,<gate>.log}`, prints a PASS/FAIL table, for pytest/vitest failures extracts failing test ids into `result.json.failures`, exits 1 on any mandatory failure; refuses to run if `gates.json` mandatory set was reduced (hash check against `.harness/gates.lock`)

---

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T005 [P] Domain errors in `src/splitease/core/errors.py`: `DomainError(code, message)` and the error codes listed in data-model.md "Error codes (core)"
- [ ] T006 [P] Money helpers in `src/splitease/core/money.py`: `format_inr(paise)->"1000.00"`, `parse_percent(str)->basis points` (data-model.md SplitInput.percent; Decimal-free integer parsing, ≤ 2 decimals), amount range check (data-model.md Expense.amount, Settlement.amount) raising `INVALID_AMOUNT`
- [ ] T007 [P] Unit tests for money helpers in `tests/unit/test_money.py` (FR-006, FR-016 formatting, Principle I)
- [ ] T008 Core value types in `src/splitease/core/model.py` (frozen dataclasses `Member`, `SplitInput`, `Expense`, `Settlement`, `Payment`; no I/O) per data-model.md
- [ ] T009 Test `tests/unit/test_core_purity.py`: `splitease.core` modules import none of `sqlite3`, `fastapi`, `random`, `datetime.now`/`time` (Principle II)
- [ ] T010 SQLite repository in `src/splitease/storage/repository.py`: schema (groups, members, expenses, expense_splits, expense_shares, settlements, seq), parameterised queries only, transaction per write, `Repository(path)` with `:memory:` support (FR-019)
- [ ] T011 FastAPI app factory in `src/splitease/api/app.py`: `create_app(db_path)`, error handlers mapping `DomainError` → 400/404 and `RequestValidationError` → 422 `VALIDATION_ERROR` (research R8), static SPA mount from `frontend/dist` if present; `src/splitease/__main__.py` runs uvicorn on 127.0.0.1:8000
- [ ] T012 Test fixtures in `tests/conftest.py`: `client` (TestClient on fresh in-memory/tmp DB), `make_group` helper

**Checkpoint**: harness runs end-to-end (empty test suites allowed to pass only lint/security).

---

## Phase 3: User Story 1 — Create group & equal split (P1) 🎯 MVP

**Goal**: create a group, add an EQUAL expense, see exact balances.
**Independent Test**: US1 acceptance scenarios 1–4 via API.

### Tests (write first)
- [ ] T013 [P] [US1] `tests/unit/test_splitting_equal.py`: FR-004 (100000/3 → 33334,33333,33333; 1 paisa/3 → 1,0,0; payer not participant), FR-009, FR-010 (`UNKNOWN_MEMBER`, `DUPLICATE_PARTICIPANT`, `EMPTY_SPLIT`)
- [ ] T014 [P] [US1] `tests/unit/test_balances.py`: FR-012, FR-013 (US1-2, US1-3 exact balances; Σ = 0)
- [ ] T015 [P] [US1] `tests/unit/test_groups_validation.py`: FR-001 (`INVALID_MEMBERS` for <2, >50, duplicate names case-insensitive/trimmed; name lengths per data-model.md Group.name, Member.name)
- [ ] T016 [P] [US1] `tests/contract/test_groups_api.py`: C1, C2, C3 status codes and payloads (US1-1), 404 `GROUP_NOT_FOUND`, 422 for bad body
- [ ] T017 [P] [US1] `tests/contract/test_expenses_equal_api.py`: C4 EQUAL (US1-2, US1-3), C7 balances, data-model.md Expense.description / Expense.amount / Expense.date bounds → 422

### Implementation
- [ ] T018 [US1] Group/member validation `validate_members(names)` in `src/splitease/core/groups.py` (data-model.md Group.name, Group.members, Member.name, Member.position)
- [ ] T019 [US1] EQUAL split + common participant validation in `src/splitease/core/splitting.py` (data-model.md Expense.splits, Expense.paid_by, Expense.shares)
- [ ] T020 [US1] Balances in `src/splitease/core/balances.py` (FR-012/FR-013)
- [ ] T021 [US1] Pydantic schemas `GroupIn`, `Group`, `ExpenseIn`, `Expense`, `Balance` in `src/splitease/api/schemas.py` (data-model.md Expense.description, Expense.amount, Expense.date, Expense.split_mode)
- [ ] T022 [US1] Routes C1, C2, C3, C4 (EQUAL), C7 in `src/splitease/api/app.py`; repository methods in `src/splitease/storage/repository.py`

---

## Phase 4: User Story 2 — Exact / percent / shares (P1)

**Goal**: uneven splits with exact remainder handling. **Independent Test**: US2-1…6.

### Tests (write first)
- [ ] T023 [P] [US2] `tests/unit/test_splitting_modes.py`: FR-005 (`SPLIT_SUM_MISMATCH`), FR-006 (10000 → 3333,3333,3334; 100 → 33,33,34; `PERCENT_SUM_INVALID` for 99.99; >2 decimals rejected), FR-007 (1:2:3 of 100000 → 16667,33333,50000; `INVALID_WEIGHT`), FR-008 tie-break by member order
- [ ] T024 [P] [US2] `tests/property/test_split_invariants.py` (Hypothesis): for random amounts/modes/participants, Σ shares = amount, all shares ≥ 0, determinism (same input twice → same output); plus random sequences of expenses + settlements (`max_examples ≥ 500`) asserting Σ balances = 0 after every operation — SC-001, FR-013
- [ ] T025 [P] [US2] `tests/contract/test_expenses_modes_api.py`: C4 for EXACT/PERCENT/SHARES success + each 400 error code; nothing persisted on error (FR-018)

### Implementation
- [ ] T026 [US2] EXACT, PERCENT, SHARES + largest-remainder in `src/splitease/core/splitting.py` (data-model.md SplitInput.amount, SplitInput.percent, SplitInput.weight)
- [ ] T027 [US2] Extend `ExpenseIn` split item schema and C4 route for all modes in `src/splitease/api/schemas.py`, `src/splitease/api/app.py`

---

## Phase 5: User Story 3 — Settle-up plan (P1)

**Goal**: greedy payment plan. **Independent Test**: US3-1…3.

### Tests (write first)
- [ ] T028 [P] [US3] `tests/unit/test_settle.py`: FR-014 (US3-1 exact plan, US3-3 empty plan, tie-break by member order, ≤ k−1 payments, 50-member plan < 100 ms)
- [ ] T029 [P] [US3] `tests/property/test_settle_invariants.py` (Hypothesis): random zero-sum balances → applying plan zeroes all, amounts > 0, ≤ k−1 payments — SC-004
- [ ] T030 [P] [US3] `tests/contract/test_settle_api.py`: C8 payload for US3-1

### Implementation
- [ ] T031 [US3] Greedy plan in `src/splitease/core/settle.py` (data-model.md Payment, research R4)
- [ ] T032 [US3] Route C8 and `settle_up` in C3 detail in `src/splitease/api/app.py`

---

## Phase 6: User Story 4 — Record settlement (P2)

### Tests (write first)
- [ ] T033 [P] [US4] `tests/unit/test_settlements.py`: FR-015 (US4-1, US4-4 over-payment flips sign, `SAME_MEMBER`)
- [ ] T034 [P] [US4] `tests/contract/test_settlements_api.py`: C6 201/400/422 (US4-2, US4-3), DELETE settlement → 405 (US4-5)

### Implementation
- [ ] T035 [US4] Settlement validation in `src/splitease/core/settlements.py` and balance integration in `src/splitease/core/balances.py` (data-model.md Settlement.from_member, Settlement.to_member, Settlement.amount)
- [ ] T036 [US4] Route C6 + schemas + repository insert (no delete) in `src/splitease/api/app.py`, `src/splitease/api/schemas.py`, `src/splitease/storage/repository.py` (data-model.md Settlement.date)

---

## Phase 7: User Story 5 — Delete expense (P2)

- [ ] T037 [P] [US5] `tests/contract/test_delete_expense_api.py`: C5 (US5-1 balances restored exactly, US5-2 `EXPENSE_NOT_FOUND`)
- [ ] T038 [US5] Route C5 + repository delete (cascade splits/shares) in `src/splitease/api/app.py`, `src/splitease/storage/repository.py`

---

## Phase 8: User Story 6 — CSV export (P3)

- [ ] T039 [P] [US6] `tests/unit/test_ledger_csv.py`: FR-016 exact expected CSV text for a fixed ledger, FR-017 formula neutralisation for `= + - @`, SC-006 determinism
- [ ] T040 [P] [US6] `tests/contract/test_export_api.py`: C9 content type, disposition header, body
- [ ] T041 [US6] CSV builder in `src/splitease/core/ledger_csv.py`; route C9 in `src/splitease/api/app.py`

---

## Phase 9: User Story 7 — Web UI (P2)

### Tests (write first)
- [ ] T042 [P] [US7] `frontend/tests/money.test.ts`: FR-022 (`"1000.5"`→100050, `"0.1"`→10, rejects `12.345`, `abc`, `-5`, `1e3`, range), `formatINR`
- [ ] T043 [P] [US7] `frontend/tests/App.test.tsx`: renders group list, create-group form validation, expense form shows API error message verbatim (US7-2) using a mocked `fetch`

### Implementation
- [ ] T044 [P] [US7] `frontend/src/money.ts` (research R6) and `frontend/src/api.ts` typed client for C1–C9
- [ ] T045 [US7] Components in `frontend/src/components/`: `GroupList.tsx`, `CreateGroupForm.tsx`, `GroupView.tsx`, `ExpenseForm.tsx` (mode selector EQUAL/EXACT/PERCENT/SHARES), `ExpenseList.tsx`, `BalancesPanel.tsx`, `SettleUpPanel.tsx` (record button), `SettlementForm.tsx`; `App.tsx`; styles `frontend/src/styles.css` — text rendering only (Principle V)
- [ ] T046 [US7] Refresh balances/settle-up after each mutation without full reload (US7-3)

---

## Phase 10: Polish & Cross-Cutting

- [ ] T047 [P] `README.md` in Part-1A: run app, run harness, layout, traceability pointer
- [ ] T048 [P] Traceability matrix `specs/001-shared-expense-splitter/traceability.md` (FR/SC → test files)
- [ ] T049 Run full harness, record in `evidence/`, then follow feedback/repair loop (constitution IV)
- [ ] T050 Run quickstart.md scenarios manually in the browser (also manual check of SC-002: group + first expense in < 2 min)

---

## Dependencies & Execution Order

- Phase 1 → Phase 2 → US1 → (US2, US3, US4, US5, US6 can proceed in parallel; all depend on US1's
  splitting/balance/route scaffolding) → US7 (needs C1–C9) → Polish.
- Within each story: tests → core → schemas/routes.

## Parallel Examples

- US1 tests: T013, T014, T015, T016, T017 together.
- US2 + US3 test writing: T023, T024, T025, T028, T029, T030 together.
- Frontend T042–T044 alongside backend US4–US6.

## Implementation Strategy

1. MVP = Phase 1–3 (US1) with harness green.
2. Add US2, US3 (P1) → harness.
3. Add US4, US5, US7 (P2), then US6 (P3) → harness.
4. Preserve the first complete generation in `evidence/initial-generation/` **before** acting on
   any harness failure; final accepted copy in `evidence/final-generation/`.
