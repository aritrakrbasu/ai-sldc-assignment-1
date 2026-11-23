# SDD command log — Part 1A (SplitEase)

Verbatim inputs given to each GitHub Spec Kit command, in order. Coding agent: Claude Code
(model `claude-opus-5-5`), Spec Kit `specify-cli` with `--integration claude --script py`.

## 1. /speckit-constitution
Input: "SplitEase: shared-expense web app. Principles: exact integer-paise money arithmetic,
pure deterministic domain core, spec-derived tests with exact assertions, harness-gated
delivery (Ruff+ESLint, Bandit+npm audit, pytest+Vitest, >=90% core coverage), simple safe API/UI.
Stack: FastAPI + React/TypeScript, SQLite."
Output: `.specify/memory/constitution.md` v1.0.0

## 2. /speckit-specify
Input: "SplitEase — a web app for friends, roommates and trip groups to record shared expenses
and settle up fairly. Users create a group with 2-50 named members. Any member can add an expense
(description, total amount in INR, payer, date) split in one of four modes: EQUAL among selected
members, EXACT amounts per member, PERCENT per member (must total 100%), or SHARES (integer
weights). The app shows each member's net balance (positive = is owed, negative = owes), a
minimum-transactions settle-up plan (who pays whom how much), lets users record a settlement
payment between two members, lets users delete an expense, and exports the group ledger as CSV.
All money is integer paise; rounding remainders are distributed deterministically; balances
always sum to zero. Includes a REST API and a React web UI."
Output: `specs/001-shared-expense-splitter/spec.md`, `checklists/requirements.md` (all items pass)

## 3. /speckit-clarify
Questions asked by the agent and answered by the student (Aritra Basu):
- Q1 Settlement larger than debt? → "Allow it" (balance flips sign)
- Q2 Can settlements be deleted? → "No, permanent" (correct with reverse settlement)
- Q3 UI amount format? → "Rupees, max 2 decimals"
Output: `## Clarifications` session 2026-11-23 in spec.md; FR-015 updated; FR-022 added;
US4 scenarios 4-5 and edge cases added.

## 4. /speckit-plan
Input: "Backend: Python 3.15, FastAPI, Pydantic v2, stdlib sqlite3 (parameterised SQL). Pure domain
package splitease.core (splitting, balances, settle-up, csv). Frontend: React 18 + TypeScript + Vite,
ESLint, Vitest; built assets served by FastAPI so one command runs the app. Harness: Ruff, Bandit,
npm audit, pytest (+coverage >=90% core, hypothesis property tests), Vitest, orchestrated by
.harness/run_harness.py writing JSON + log to evidence/."
Output: plan.md, research.md (R1-R8), data-model.md, contracts/api.md, quickstart.md.
Note: research R5 records the switch React 18 -> 19 (current major, verified with `npm view`).
