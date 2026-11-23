# Feature Specification: SplitEase — Shared Expense Splitter

**Feature Branch**: `001-shared-expense-splitter`

**Created**: 2026-11-23

**Status**: Draft

**Input**: User description: "SplitEase — a web app for friends, roommates and trip groups to record shared expenses and settle up fairly. Users create a group with 2-50 named members. Any member can add an expense (description, total amount in INR, payer, date) split in one of four modes: EQUAL among selected members, EXACT amounts per member, PERCENT per member (must total 100%), or SHARES (integer weights). The app shows each member's net balance (positive = is owed, negative = owes), a minimum-transactions settle-up plan (who pays whom how much), lets users record a settlement payment between two members, lets users delete an expense, and exports the group ledger as CSV. All money is integer paise; rounding remainders are distributed deterministically; balances always sum to zero. Includes a REST API and a React web UI."

## Clarifications

### Session 2026-11-23

- Q: If a member records a settlement larger than what they owe, what should happen? → A: Allow it; the balance flips sign (receiver now owes payer the excess).
- Q: Can a recorded settlement be deleted? → A: No, settlements are permanent; mistakes are corrected by recording a reverse settlement.
- Q: Which amount format does the web form accept? → A: Rupees with at most 2 decimals (e.g. `1000`, `1000.5`, `1000.50`), converted to paise by exact string parsing; 3+ decimals rejected.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create a group and split an expense equally (Priority: P1)

A flatmate creates a group "Flat 4B" with members Asha, Bilal and Chen, then records that Asha
paid ₹1,000.00 for groceries shared equally by all three. The app shows exactly how much each
person owes or is owed.

**Why this priority**: This is the smallest slice that delivers the core value — knowing who
owes whom after a shared purchase.

**Independent Test**: Create a group, add one EQUAL expense, read balances; verify exact paise.

**Acceptance Scenarios**:

1. **Given** no groups exist, **When** a user creates group "Flat 4B" with members
   ["Asha", "Bilal", "Chen"], **Then** the group is saved with those 3 members in that order
   and every member's balance is ₹0.00.
2. **Given** group "Flat 4B", **When** Asha adds an EQUAL expense of 100000 paise among all 3
   members, **Then** the shares are Asha 33334, Bilal 33333, Chen 33333 paise (remainder 1
   paisa goes to the first participant in member order) and balances are
   Asha +66666, Bilal −33333, Chen −33333.
3. **Given** group "Flat 4B", **When** Asha adds an EQUAL expense of 90000 paise among only
   Bilal and Chen, **Then** shares are Bilal 45000, Chen 45000, Asha 0 and balances are
   Asha +90000, Bilal −45000, Chen −45000.
4. **Given** any group state, **When** balances are read, **Then** the sum of all balances is
   exactly 0.

---

### User Story 2 - Split unevenly: exact, percent and shares (Priority: P1)

A trip group splits a hotel bill by number of nights (shares), a dinner by exact amounts and
a cab by agreed percentages.

**Why this priority**: Real groups rarely split everything equally; without these modes the
app is not useful for trips or couples.

**Independent Test**: Add one expense per mode and verify exact shares and balances.

**Acceptance Scenarios**:

1. **Given** members A, B, C, **When** A adds an EXACT expense of 50000 paise with
   B=20000, C=30000, **Then** shares are B 20000, C 30000 and balances are A +50000,
   B −20000, C −30000.
2. **Given** an EXACT expense whose amounts sum to 49999 for a total of 50000, **When** it is
   submitted, **Then** it is rejected with error code `SPLIT_SUM_MISMATCH` and nothing is saved.
3. **Given** members A, B, C, **When** A adds a PERCENT expense of 10000 paise with
   A=33.33%, B=33.33%, C=33.34%, **Then** shares are A 3333, B 3333, C 3334.
4. **Given** members A, B, C, **When** A adds a PERCENT expense of 100 paise with
   A=33.33%, B=33.33%, C=33.34% **Then** shares are A 33, B 33, C 34 (largest-remainder
   rounding, ties broken by member order) and they sum to 100.
5. **Given** PERCENT values summing to 99.99%, **When** submitted, **Then** it is rejected with
   `PERCENT_SUM_INVALID`.
6. **Given** members A, B, C, **When** A adds a SHARES expense of 100000 paise with weights
   A=1, B=2, C=3, **Then** shares are A 16667, B 33333, C 50000 (sum 100000).

---

### User Story 3 - See who should pay whom (Priority: P1)

Before leaving the trip, the group opens "Settle up" and sees a short list of payments that
clears every balance.

**Why this priority**: Turning balances into concrete payments is the reason people use the app.

**Independent Test**: Seed balances, request the plan, apply it virtually and verify every
balance becomes 0.

**Acceptance Scenarios**:

1. **Given** balances A +66666, B −33333, C −33333, **When** the plan is requested, **Then**
   it is exactly [B→A 33333, C→A 33333].
2. **Given** any balances, **When** the plan is applied, **Then** every member's balance is 0,
   the plan has at most (number of members with non-zero balance − 1) payments, and every
   payment amount is a positive integer.
3. **Given** all balances are 0, **When** the plan is requested, **Then** the plan is empty.

---

### User Story 4 - Record a settlement payment (Priority: P2)

Bilal pays Asha ₹333.33 by UPI and records it so the balances update.

**Why this priority**: Without recording repayments, balances never go back to zero.

**Independent Test**: Record a settlement and verify both balances change by the exact amount.

**Acceptance Scenarios**:

1. **Given** balances A +66666, B −33333, **When** a settlement B→A of 33333 is recorded,
   **Then** balances become A +33333, B 0.
2. **Given** a settlement where payer equals receiver, **When** submitted, **Then** it is
   rejected with `SAME_MEMBER`.
3. **Given** a settlement with amount 0 or negative, **When** submitted, **Then** it is
   rejected as invalid input.
4. **Given** balances A +33333, B −33333, **When** a settlement B→A of 50000 is recorded,
   **Then** it is accepted and balances become A −16667, B +16667.
5. **Given** a recorded settlement, **When** a user wants to undo it, **Then** there is no
   delete operation; they record a reverse settlement (A→B of the same amount) instead.

---

### User Story 5 - Delete a mistaken expense (Priority: P2)

A member deletes an expense that was entered twice.

**Why this priority**: Mistakes happen; balances must stay correct.

**Independent Test**: Add then delete an expense; balances return to their prior values.

**Acceptance Scenarios**:

1. **Given** an expense exists, **When** it is deleted, **Then** it no longer appears in the
   ledger and all balances equal their values before it was added.
2. **Given** an expense id that does not exist in the group, **When** deletion is requested,
   **Then** the response is "not found" with `EXPENSE_NOT_FOUND`.

---

### User Story 6 - Export the ledger as CSV (Priority: P3)

The group treasurer downloads the ledger to keep in a spreadsheet.

**Why this priority**: Useful for record keeping but not needed to split or settle.

**Independent Test**: Export a group with known entries and compare to an expected CSV.

**Acceptance Scenarios**:

1. **Given** a group with expenses and settlements, **When** CSV is exported, **Then** the
   file has the header `date,type,description,paid_by,amount_inr,split_mode,participants`
   and one row per entry, ordered by date then creation order, amounts formatted with two
   decimals (e.g. `1000.00`).
2. **Given** an expense description that starts with `=`, `+`, `-` or `@`, **When** exported,
   **Then** the cell is prefixed with a single quote `'` to prevent formula execution.

---

### User Story 7 - Use it all from a web page (Priority: P2)

A non-technical user does all of the above in a browser without using the API directly.

**Why this priority**: The target users are friends and flatmates, not developers.

**Independent Test**: Open the UI, create a group, add an expense, view balances and the
settle-up plan, record a settlement, download CSV.

**Acceptance Scenarios**:

1. **Given** the app is running, **When** a user opens the home page, **Then** they can list
   groups and create a new one.
2. **Given** a group page, **When** the user adds an expense with an invalid split, **Then**
   the form shows the validation message returned by the system and nothing is saved.
3. **Given** a group page, **When** balances change, **Then** the balances and settle-up
   panels refresh without a full page reload.

---

### Edge Cases

- Amount of 1 paisa split EQUAL among 3 members → shares 1, 0, 0 (first in member order gets
  the remainder); balances still sum to 0.
- Payer is not among participants → allowed; payer's share is 0.
- A participant or payer id not belonging to the group → rejected with `UNKNOWN_MEMBER`.
- Duplicate participant in a split → rejected with `DUPLICATE_PARTICIPANT`.
- Split with no participants → rejected with `EMPTY_SPLIT`.
- SHARES with any weight ≤ 0 or all weights 0 → rejected with `INVALID_WEIGHT`.
- PERCENT with more than 2 decimal places or a negative value → rejected as invalid input.
- EXACT with a negative per-member amount → rejected as invalid input.
- Amount above ₹1 crore (1,000,000,000 paise) or below 1 paisa → rejected as invalid input.
- Group with fewer than 2 or more than 50 members, or duplicate member names
  (case-insensitive, trimmed) → rejected (`INVALID_MEMBERS`).
- UI amount input `12.345`, `abc`, `-5` or `1e3` → rejected in the form; `0.1` → 10 paise
  exactly; `1000.5` → 100050 paise.
- Settlement exceeding the payer's debt → accepted; balances flip sign and still sum to 0.
- Empty or whitespace-only description, or longer than 120 characters → rejected.
- Settle-up ties (two creditors with equal balance) → ordered by member order so the plan is
  identical on every run.

## Requirements *(mandatory)*

### Functional Requirements

**Groups & members**
- **FR-001**: Users MUST be able to create a group with a name (1–60 chars) and 2–50 member
  names (each 1–40 chars, unique case-insensitively after trimming). Member order is the order
  given and is called *member order*.
- **FR-002**: Users MUST be able to list all groups and view one group with its members,
  expenses, settlements, balances and settle-up plan.

**Expenses & splitting**
- **FR-003**: Users MUST be able to add an expense with description (1–120 chars), amount in
  paise (integer, 1 to 1,000,000,000), payer (a group member), date (calendar date) and a
  split definition.
- **FR-004**: EQUAL split: amount is divided among the selected participants (≥1). Each gets
  `amount // n`; the remainder `amount % n` is given as +1 paisa to the first `remainder`
  participants in member order.
- **FR-005**: EXACT split: each participant has an integer paise amount ≥ 0; the amounts MUST
  sum exactly to the expense amount, otherwise reject with `SPLIT_SUM_MISMATCH`.
- **FR-006**: PERCENT split: each participant has a percentage with at most 2 decimal places
  (≥ 0); percentages MUST sum to exactly 100.00, otherwise reject with `PERCENT_SUM_INVALID`.
  Shares are computed by the largest-remainder rule (FR-008).
- **FR-007**: SHARES split: each participant has an integer weight ≥ 1; shares are computed by
  the largest-remainder rule (FR-008) proportional to weight.
- **FR-008**: Largest-remainder rule: each participant first receives the floor of their exact
  proportional amount; the leftover paise are given one each to participants with the
  largest fractional remainder, ties broken by member order.
- **FR-009**: For every accepted expense, the sum of participant shares MUST equal the amount.
- **FR-010**: Participants and payer MUST belong to the group (`UNKNOWN_MEMBER`); a participant
  MUST NOT appear twice (`DUPLICATE_PARTICIPANT`); a split with zero participants MUST be rejected
  (`EMPTY_SPLIT`).
- **FR-011**: Users MUST be able to delete an expense; unknown ids yield `EXPENSE_NOT_FOUND`.

**Balances & settle-up**
- **FR-012**: A member's net balance = (total paid for expenses) − (total of their expense
  shares) + (settlements they paid) − (settlements they received). Positive means the member
  is owed money.
- **FR-013**: The sum of all net balances in a group MUST be exactly 0 after every operation.
- **FR-014**: The settle-up plan MUST be computed by repeatedly matching the member with the
  largest debt to the member with the largest credit, paying the smaller of the two absolute
  values, ties broken by member order. The plan MUST zero every balance and contain at most
  (k − 1) payments where k is the number of members with non-zero balance.
- **FR-015**: Users MUST be able to record a settlement (payer, receiver, amount in paise
  1–1,000,000,000, date). Payer and receiver MUST be different (`SAME_MEMBER`) members of the
  group. A settlement larger than the payer's current debt MUST be accepted (the balance flips
  sign). Settlements are immutable: the system MUST NOT offer a delete or edit operation for them.
- **FR-022**: The UI MUST accept amounts as rupees with at most 2 decimal places, convert them
  to paise by exact decimal string parsing (never binary floating point), and reject inputs with
  3 or more decimals, non-numeric characters or values outside the allowed range before sending.

**Export**
- **FR-016**: Users MUST be able to export a group ledger as CSV with the columns and ordering
  defined in User Story 6, amounts rendered as rupees with exactly two decimals.
- **FR-017**: CSV text cells beginning with `=`, `+`, `-` or `@` MUST be prefixed with `'`.

**Errors, persistence & interface**
- **FR-018**: Invalid input MUST be rejected without partial changes, with a machine-readable
  error code and a human-readable message.
- **FR-019**: Data MUST persist across application restarts.
- **FR-020**: All capabilities MUST be available both programmatically (HTTP API) and through a
  browser UI; the UI MUST display amounts in rupees (₹, two decimals) while sending paise.
- **FR-021**: Identical sequences of operations MUST produce identical balances, plans and CSV
  output.

### Key Entities

- **Group**: id, name, ordered list of members, created timestamp.
- **Member**: id, display name, position in member order; belongs to one group.
- **Expense**: id, group, description, amount (paise), payer, date, split mode, split inputs
  (participants with amount / percent / weight), computed shares.
- **Settlement**: id, group, payer, receiver, amount (paise), date.
- **Balance** (derived): member → net paise.
- **Settle-up Payment** (derived): from member, to member, amount (paise).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of accepted expenses have shares summing exactly to the expense amount, and
  100% of group states have balances summing to exactly 0 (verified by automated property tests
  over at least 500 random operations).
- **SC-002**: A new user can create a group and record a first expense in under 2 minutes.
- **SC-003**: The settle-up plan for a 50-member group appears in under 1 second.
- **SC-004**: Applying the settle-up plan leaves every member at exactly ₹0.00 in 100% of tested
  cases.
- **SC-005**: Every invalid input listed in Edge Cases is rejected with its specified error
  code and leaves stored data unchanged.
- **SC-006**: Repeating the same sequence of operations twice yields byte-identical CSV exports.

## Assumptions

- Single currency (INR); no currency conversion.
- No user accounts or authentication in this version: anyone who can open the app can edit any
  group (intended for a trusted local/household setting).
- Editing an existing expense is out of scope; users delete and re-add instead.
- Members cannot be added or removed after group creation in this version.
- The settle-up plan is a greedy plan bounded by k−1 payments; it is not guaranteed to be the
  mathematical minimum number of payments (that problem is NP-hard), but it is deterministic.
- Dates are calendar dates without time zone; future dates are allowed.
- Runs locally on one machine for one household or trip group at a time.
