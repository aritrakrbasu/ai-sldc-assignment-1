# SDD command log — Part 1B (MoneyLens)

Verbatim inputs given to each GitHub Spec Kit command, in order. Coding agent: Claude Code
(model `claude-opus-5-5`), Spec Kit `specify-cli` with `--integration claude --script py`.

## 1. /speckit-constitution
Input: "MoneyLens: AI finance inbox for Indian bank/UPI SMS using Gemini. Principles: contract-first
JSON output, grounded extraction (no invented values; LLM never does arithmetic), safety/privacy
guardrails (mask OTPs/card numbers before the model, flag phishing, ignore injected instructions,
user-confirmed external actions, key only from env), evaluation-gated delivery (3-layer harness,
repeats, service errors separated, no threshold lowering), simplicity/reproducibility."
Output: `.specify/memory/constitution.md` v1.0.0

## 2. /speckit-specify
Input: "MoneyLens — an AI-powered personal finance inbox for Indian bank and UPI SMS. A user pastes
or uploads a batch of SMS (up to 50). For each message the AI classifies it as TRANSACTION, OTP,
PROMOTION, BILL_REMINDER, PHISHING_SUSPECT or OTHER. For transactions it extracts amount,
debit/credit, merchant or counterparty, account last-4 digits, transaction date, payment channel
and a spend category. For bill reminders it extracts amount due and due date. OTPs and full card
numbers are masked before anything is sent to the AI and never appear in output; phishing/scam SMS
are flagged with reasons and never treated as transactions; instructions embedded inside SMS are
ignored. Parsed transactions are saved and shown on a dashboard with spend by category and recent
transactions. The user can ask natural-language spending questions (e.g. "How much did I spend on
food last week?"); the AI translates the question into a structured query which the app executes
deterministically, and asks for clarification when the question is ambiguous or out of scope. The
user can send a parsed debit to a SplitEase group (Part 1A app) as a shared expense after explicit
confirmation. Includes a REST API, React web UI and an evaluation harness."
Output: `specs/001-sms-finance-inbox/spec.md` (FR-001..FR-020, SCH, INV-1..9, PROP-1..6, GR-1..6,
evaluation threshold), `checklists/requirements.md` (all pass).

## 3. /speckit-clarify
Questions asked by the agent and answered by the student (Aritra Basu):
- Q1 Evaluation threshold strictness? → "Stricter" (R=3, 100% structural, 100% safety, ≥95% cases, mean ≥0.90)
- Q2 Default period when none given? → "This month to date"
- Q3 Gemini model? → "Auto: best Flash model" (newest stable flash for the key, temperature 0.2)
Output: Clarifications section, Evaluation Threshold (c)/(d) raised, FR-009 updated.

## 4. /speckit-plan
Input: "Backend: Python 3.15, FastAPI, Pydantic v2, stdlib sqlite3. Gemini via google-genai SDK with
JSON-schema structured output; pluggable LLM client with a deterministic fake for tests. Pure core
(masking, amount/date parsing, grounding post-validator, deterministic query executor, dashboard
aggregation). Prompts versioned in prompts/. JSON Schemas in contracts used by both app and harness.
Frontend React + TS + Vite like Part 1A. Harness: .harness/evaluate.py (dataset -> app -> schema ->
invariants/properties -> semantic scoring -> threshold, R=3, service errors separated) plus
.harness/run_harness.py deterministic gates (ruff, bandit, pytest, eslint, tsc, vitest, npm audit)."
Output: plan.md, research.md (R1-R9), data-model.md, contracts/{api.md, 4 JSON Schemas}, quickstart.md.

## 5. /speckit-tasks
Input: (none). Output: tasks.md — 43 tasks; dataset, threshold and evaluation harness are
foundational (written before AI app logic).

## 6. /speckit-analyze
Result: 1 CRITICAL, 1 HIGH, 3 MEDIUM, 1 LOW. Student approved "apply all 6":
- D1 CRITICAL evidence files not leak-scanned -> T009 adds EVIDENCE_LEAK scan (INV-6)
- E1 HIGH Message.phishing_reasons uncited -> T015 cites it
- E2 MED SC-004 untested -> T041 records 20-message batch timing
- F1 MED INVALID_QUESTION vs 422 -> unified on 422 VALIDATION_ERROR; schema enum updated
- C1 MED ALREADY_SHARED not in spec -> added to FR-016
- C2 LOW SC-006 manual -> noted in T043

## 7. /speckit-implement (in progress)
- Setup T001-T005; evaluation assets T006-T010 written and hash-locked BEFORE app logic.
- Spec revision during harness writing (pre-implementation): FR-002(b)/INV-6 long-number rule
  narrowed so date-times are not masked (recorded in spec Clarifications).
- research R3 amended: client-side rate limiter MONEYLENS_RPM (default 10/min).
- Evaluation: initial-generation FAIL (P14 guardrail) -> prompt v2 repair -> re-evaluation PASS
  (38/38, mean 1.0). SC-004 61.39 s (unmet by 1.4 s, disclosed). Human decision pending.
