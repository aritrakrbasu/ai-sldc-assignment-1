# MoneyLens Constitution

## Core Principles

### I. Contract-First AI Output (NON-NEGOTIABLE)
- Every model response MUST be parsed into a versioned JSON output schema
  (`contracts/*.schema.json`) and validated before the application uses it. Field names, types
  and enumerations MUST stay stable even when the model's wording changes.
- Output that fails validation MUST NOT be passed downstream. The application MUST return an
  explicit `status: "error"` result with a reason code and MUST NOT guess.
- Money MUST be represented as integer paise. Dates MUST be ISO-8601 `YYYY-MM-DD`.

Rationale: non-deterministic text becomes testable only when its structure is fixed.

### II. Grounded Extraction, No Invention
- Every extracted value MUST be grounded in the input text. An amount, account suffix or
  merchant MUST be traceable to characters that actually appear in the SMS. Values that are
  not grounded MUST be set to `null`, never invented.
- Numbers in answers to spending questions MUST be computed deterministically by application
  code from stored transactions. The model MUST only translate the question into a structured
  query; it MUST NOT do the arithmetic.

Rationale: LLM hallucination in finance is a correctness and trust failure. Grounding checks
are deterministic and binary.

### III. Safety & Privacy Guardrails (NON-NEGOTIABLE)
- OTP codes and full card or account numbers (≥ 9 consecutive digits) MUST be masked
  **before** any text is sent to the model, and MUST NOT appear in any output, log or evidence
  file.
- Suspected phishing or scam messages MUST be flagged with at least one machine-readable
  reason. The application MUST NOT extract them as normal transactions or forward them anywhere.
- Instructions embedded in SMS text (prompt injection) MUST be treated as data, never followed.
- Actions with external effects (sending an expense to SplitEase) MUST require an explicit user
  confirmation for each item and MUST be limited to valid DEBIT transactions.
- The API key MUST come from the environment (`GEMINI_API_KEY`, loaded from a git-ignored
  `.env`), and MUST never be committed, logged or written to evidence.

### IV. Evaluation-Gated Delivery
- A single evaluation harness (`.harness/evaluate.py`) MUST score the application against
  `evals/dataset.json` (≥ 15 cases) in three layers: structural (schema), property/invariant,
  and semantic/quality. It MUST then produce PASS/FAIL against the threshold declared in the
  spec **before** the final evaluation.
- Each case MUST be run multiple times (repeats declared in the spec) to expose
  non-determinism. A case passes only if every repeat passes.
- Model or service failures (network, quota, 5xx, timeouts) MUST be recorded separately as
  `SERVICE_ERROR` and MUST NOT be counted as application passes or failures. A run with too
  many service errors is `INCONCLUSIVE`, not PASS.
- Thresholds, cases and expected results MUST NOT be lowered, removed or edited to obtain a
  PASS. Changes require a spec revision with a dated rationale.
- A deterministic local harness (Ruff, Bandit, pytest with mocked model calls) MUST also pass.

### V. Simplicity & Reproducibility
- Model, model version, temperature and prompt version MUST be configurable and MUST be
  recorded in every evaluation result.
- Prompts MUST live in versioned files under `prompts/`, not inline string literals scattered
  through the code.
- YAGNI: no user accounts, no reading SMS directly from phones, no bank integrations.

## Technology & Quality Constraints

- Backend: Python 3.12+ (developed on 3.15) with FastAPI and Pydantic v2. Model access via the
  Google Gemini API (`google-genai` SDK). Storage: SQLite through stdlib `sqlite3` with
  parameterised queries.
- Frontend: React + TypeScript (Vite), same toolchain as Part 1A.
- A batch of up to 50 SMS per request. A single SMS is at most 1,000 characters.
- Unit and contract tests MUST NOT call the real model. They use a deterministic fake client.

## Development Workflow & Quality Gates

- Flow: constitution → specify → clarify → plan → tasks → analyze → implement → evaluate →
  structured failure evidence → repair → re-evaluate → human ACCEPT/REJECT.
- The first generation MUST be preserved in `evidence/initial-generation/` before any
  evaluation-driven repair. The accepted version goes in `evidence/final-generation/`.
- Every evaluation run MUST be stored under `evidence/eval-runs/`. The latest accepted run is
  copied to `evidence/eval-results.json`.
- The final ACCEPT/REJECT decision is made by the human student.

## Governance

- This constitution supersedes other practices for MoneyLens. Every plan MUST contain a
  Constitution Check.
- Amendments require a semantic version bump and a dated note.

**Version**: 1.0.0 | **Ratified**: 2026-11-23 | **Last Amended**: 2026-11-23
