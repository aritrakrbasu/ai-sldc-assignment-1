# Data Model: MoneyLens

The canonical output contracts are the JSON Schemas in `contracts/`. This file covers storage
and the extra validation rules.

## Message (table `messages`)
| Field | Type | Rules |
|-------|------|-------|
| id | int | assigned |
| content_hash | str | SHA-256 of `masked_text`; UNIQUE (FR-008 duplicate rule) |
| masked_text | str | ≤ 1,000 chars before masking (FR-001); only masked text is stored (FR-002) |
| kind | enum | spec Output Schema Contract `kind` |
| reference_date | date | ISO |
| model, model_version, temperature, prompt_version | str/float | FR-009 |
| created_at | str | ISO-8601 UTC |

## Transaction (table `transactions`, 1:1 with a TRANSACTION message)
| Field | Type | Rules |
|-------|------|-------|
| message_id | int | FK Message, UNIQUE |
| amount_paise | int | 1 … 10,000,000,000; grounded (INV-3) |
| direction | enum | DEBIT \| CREDIT |
| merchant | str \| null | 1–80 chars; grounded (INV-5) |
| account_last4 | str \| null | `^\d{4}$`; grounded (INV-4) |
| txn_date | date \| null | ≤ reference_date (INV-7) |
| channel | enum | UPI, CARD, NETBANKING, ATM, WALLET, OTHER |
| category | enum | 13 categories (spec) |
| shared_expense_id | int \| null | SplitEase expense id once shared (FR-015) |

## BillReminder (table `bills`)
| Field | Type | Rules |
|-------|------|-------|
| message_id | int | FK Message, UNIQUE |
| amount_due_paise | int \| null | grounded (INV-3) |
| due_date | date \| null | valid date |
| biller | str \| null | 1–80 chars |

## Phishing reasons
Stored as a JSON array on the message row (`Message.phishing_reasons`). Non-empty for PHISHING_SUSPECT, otherwise null.

## Query (not stored)
`ModelQueryOutput` → validated → executed by `core/query_exec.py` over transactions with
`txn_date` in `[date_from, date_to]` (transactions with null `txn_date` use the message's
`reference_date`), direction match, category ∈ categories (or all), merchant substring
(case-insensitive).

| metric | answer.value_paise | answer.count | answer.items |
|--------|-------------------|--------------|--------------|
| TOTAL | Σ amount | n | [] |
| COUNT | null | n | [] |
| AVERAGE | Σ // n (floor, 0 if n=0) | n | [] |
| LARGEST | max amount (null if n=0) | n | [the top transaction] |
| LIST | Σ amount | n | up to 20 most recent |
| TOP_MERCHANTS | Σ amount | n | up to 5 `{merchant, value_paise, count}` by value desc, then name asc |

## SplitRequest (API only)
`{transaction_id, group_id, paid_by, participants[], confirm: bool}`. Outcome codes:
`CONFIRMATION_REQUIRED`, `NOT_A_DEBIT`, `ALREADY_SHARED`, `SPLITEASE_UNAVAILABLE`, pass-through
SplitEase codes.

## Error / reason codes
Parse: `MESSAGE_TOO_LONG`, `MODEL_OUTPUT_INVALID` (sub-reasons `SCHEMA_INVALID`, `NOT_JSON`,
`AMOUNT_NOT_GROUNDED`), `MODEL_UNAVAILABLE`, `DUPLICATE`. Batch: `INVALID_BATCH`. Query:
`MODEL_OUTPUT_INVALID`, `MODEL_UNAVAILABLE`. An empty or > 300-character question is rejected at the API with
422 `VALIDATION_ERROR` (contracts/api.md M4).
