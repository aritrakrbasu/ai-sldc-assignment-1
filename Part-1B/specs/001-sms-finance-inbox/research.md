# Research: MoneyLens

Verified locally on 2026-11-23: a Python 3.15.1 venv installs google-genai 3.6.1, fastapi
0.165.0, pydantic 2.14.4, jsonschema 4.26.0, httpx 0.28.1 and python-dotenv 1.2.4.
`google.genai.types.GenerateContentConfig` exposes `temperature`, `system_instruction`,
`response_mime_type`, `response_schema`, `response_json_schema`, `thinking_config` and `seed`.
`Client.models.list()` and `Client.models.generate_content(model, contents, config)` exist, and
errors are raised as `google.genai.errors.ClientError` / `ServerError` (subclasses of `APIError`).

## R1. Model selection (clarification Q3)
- **Decision**: At setup, `scripts/select_model.py` lists models available to the key and picks
  the newest stable model whose id contains `flash` and that supports `generateContent`. It
  excludes ids containing `preview`, `exp`, `lite`, `tts`, `image`, `live` or `audio`. The result
  is written to `.env` as `MONEYLENS_MODEL`. Temperature is 0.2.
- **Rationale**: The student asked for automatic selection. The model id is not hard-coded from
  memory, which avoids naming a model that does not exist or is not available to this key.
- **Status**: the real model id is recorded in `evidence/harness-log.md` once the key is set.

## R2. Structured output
- **Decision**: Send `response_mime_type="application/json"` plus
  `response_json_schema=<contracts/model_*_output.schema.json>`. Always re-validate with
  `jsonschema` (Draft 2020-12). If the service rejects the schema (unsupported keyword), fall back
  to JSON mode with the schema embedded in the prompt. Validation stays mandatory either way.
- **Rationale**: Constitution I. Model-side constraints reduce errors, but they are never trusted.

## R3. One call per message, bounded concurrency
- **Decision**: One model call per SMS, at most 4 in flight, with retry and exponential backoff
  on 429/5xx/timeout (3 attempts, 2 s → 8 s). After that, `MODEL_UNAVAILABLE`.
- **Rationale**: A bad message cannot corrupt its neighbours, results map 1:1 to cases (INV-9),
  and service failures stay per message. Batch prompts were rejected because one malformed
  response would fail every message.
- **Amendment (2026-11-23, before implementation)**: a client-side limiter
  (`MONEYLENS_RPM`, default 10 requests/minute) spaces calls so that free-tier quotas are not
  exceeded during evaluation. Retries still follow the policy above.

## R4. Masking before the model (GR-1)
- **Decision**: Regexes. OTP codes are 4–8 digits within 40 characters of `otp|one time
  password|verification code|passcode|pin|code`, replaced by `[OTP]`. Long numbers are
  `\d{9,}` or `\d{4}(?:[ -]\d{4}){2,3}` (spec FR-002(b) revision), replaced by `XXXX` + last 4 digits. Masking runs first. A final leak scan
  re-checks every outgoing prompt and every result.
- **Alternatives**: Asking the model to redact. Rejected, because the secret would already have
  left the device.

## R5. Grounding post-validator
- **Decision**: `amounts.find_amounts(text)` extracts every `(Rs\.?|INR|₹)\s*[\d,]+(\.\d{1,2})?`
  (prefix or suffix forms) as paise. The extracted amount must be in that set, otherwise
  `MODEL_OUTPUT_INVALID` with reason `AMOUNT_NOT_GROUNDED`. `account_last4` must occur in the
  text, otherwise it is set to null. `merchant` must share a ≥ 3-character token with the text,
  otherwise null. Dates after the reference date are set to null.
- **Rationale**: Deterministic, binary, and catches hallucination (constitution II).

## R6. Q&A
- **Decision**: The model receives the question, the reference date and its weekday, the
  category enum and the period rules (FR-012). It returns `ModelQueryOutput`. The app validates
  that `date_from ≤ date_to ≤ reference_date` and then executes the query in Python over stored
  transactions.
- **Note**: The model computes date ranges such as "last week", so date errors become
  semantic/property failures that the harness detects (INV-8 + filter score).

## R7. Evaluation harness design
- **Decision**: `.harness/evaluate.py` loads `evals/dataset.json` and `evals/threshold.json`
  (hash-locked), runs each case R times through the real application functions
  (`moneylens.ai.parser.parse_batch` / `moneylens.ai.qa.answer_question`), then applies:
  - **Layer 1**: `jsonschema` against `parse_result`/`query_result`.
  - **Layer 2**: independent re-implementations of INV/PROP in `.harness/checks/properties.py`,
    which does not import app validators.
  - **Layer 3**: weighted field scoring against ground truth in `.harness/checks/semantic.py`.

  It aggregates per spec and writes `evidence/eval-runs/<ts>/eval-results.json` plus a
  `failures.md` for the coding agent. Q&A cases run against the fixed transaction fixture in a
  temporary database.
- **Service errors**: any `MODEL_UNAVAILABLE` result marks that repeat `SERVICE_ERROR`. It is
  excluded from the pass/fail counts, and the run is INCONCLUSIVE if the error ratio exceeds 10%.

## R8. SplitEase integration
- **Decision**: `httpx` POST to `{SPLITEASE_URL}/api/groups/{gid}/expenses` with `split_mode:
  EQUAL`. The amount is the same integer paise (both apps use paise). The description is the
  merchant, truncated to 120 characters, or "Bank transaction". The date is the transaction
  date, or today if it is null. Groups and members are read via `GET /api/groups[/{id}]`.
  Tests use a fake transport (`httpx.MockTransport`).

## R9. Frontend
- **Decision**: Reuse Part 1A's toolchain. TypeScript is pinned to `~6.0` because the
  typescript-eslint peer range is `<6.1`, as found in Part 1A.
