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
