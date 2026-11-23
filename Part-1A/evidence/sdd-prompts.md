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
