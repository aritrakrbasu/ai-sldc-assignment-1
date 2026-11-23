# Harness feedback — run `20261123T172755Z_initial-generation`

Overall: **FAIL**. Gates failed: lint-python, security-python, tests-frontend

Rules for the coding agent (constitution III/IV): fix the implementation. Do NOT edit
tests, specs, thresholds or harness config to make this pass.

## Gate `lint-python` (lint) — exit 1

Output tail:

```text
src\moneylens\ai\parser.py:1:101: E501 Line too long (101 > 100)
tests\unit\test_amounts_dates.py:3:1: I001 [*] Import block is un-sorted or un-formatted
Found 2 errors.
[*] 1 fixable with `--fix`.
```

## Gate `security-python` (security) — exit 1

Output tail:

```text
Run started:2026-11-23 17:28:11.374959+00:00

Test results:
>> Issue: [B608:hardcoded_sql_expressions] Possible SQL injection vector through string-based query construction.
   Severity: Medium   Confidence: Low
   CWE: CWE-89 (https://cwe.mitre.org/data/definitions/89.html)
   More Info: https://bandit.readthedocs.io/en/1.9.4/plugins/b608_hardcoded_sql_expressions.html
   Location: src\moneylens\storage\repository.py:116:17
115	    def list_transactions(self, limit: int | None = None) -> list[dict]:
116	        sql = (f"SELECT {TXN_COLUMNS} FROM transactions t JOIN messages m ON m.id = t.message_id "  # noqa: S608
117	               "ORDER BY COALESCE(t.txn_date, m.reference_date) DESC, t.id DESC")
118	        params: tuple = ()

--------------------------------------------------
>> Issue: [B608:hardcoded_sql_expressions] Possible SQL injection vector through string-based query construction.
   Severity: Medium   Confidence: Medium
   CWE: CWE-89 (https://cwe.mitre.org/data/definitions/89.html)
   More Info: https://bandit.readthedocs.io/en/1.9.4/plugins/b608_hardcoded_sql_expressions.html
   Location: src\moneylens\storage\repository.py:134:18
133	            row = self._conn.execute(
134	                f"SELECT {TXN_COLUMNS} FROM transactions t JOIN messages m "  # noqa: S608
135	                "ON m.id = t.message_id WHERE t.id = ?", (tid,)).fetchone()
136	        return dict(row) if row else None

--------------------------------------------------

Code scanned:
	Total lines of code: 785
	Total lines skipped (#nosec): 0
	Total potential issues skipped due to specifically being disabled (e.g., #nosec BXXX): 0

Run metrics:
	Total issues (by severity):
		Undefined: 0
		Low: 1
		Medium: 2
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 1
		Medium: 2
		High: 0
Files skipped (0):

[main]	INFO	profile include tests: None
[main]	INFO	profile exclude tests: None
[main]	INFO	cli include tests: None
[main]	INFO	cli exclude tests: None
[main]	INFO	using config: .harness/bandit.yaml
[main]	INFO	running on Python 3.15.1
```

## Gate `tests-frontend` (tests) — exit 1

### Failing test `tests/App.test.tsx::Split dialog (US5) > requires preview then explicit confirmation`
- Observed (failure): Found multiple elements with the text: Riya  Here are the matching elements:  Ignored nodes: comments, script, style <option   value="11" >   Riya </option>  Ignored nodes: comments, script, style <span>   Riya </span>  (If this is intentional, then use the `*AllBy*` variant of the query (like `queryAllByText`, `getAllByText`, or `findAllByText`)).  Ignored nodes: comments, script, style <div   aria-labelledby="split-h"   aria-modal="true"   class="card dialog"   role="dialog" >   <h2     id="sp

```text
    </label>
  </fieldset>
  <div
    class="row"
  >
    <button>
      Cancel
    </button>
    <button
      class="primary"
    >
      Preview
    </button>
  </div>
</div>

Ignored nodes: comments, script, style
<div
  aria-labelledby="split-h"
  aria-modal="true"
  class="card dialog"
  role="dialog"
>
  <h2
    id="split-h"
  >
    Split in SplitEase
  </h2>
  <p
    class="muted small"
  >
    Swiggy
     · 
    ₹250.00
     · 
    2026-11-18
  </p>
  <label>
    Group
    <select>
      <option
        value="1"
      >
        Flat
      </option>
    </select>
  </label>
  <label>
    Paid by
    <select>
      <option
        value="11"
      >
        Riya
      </option>
      <option
        value="12"
      >
        Sam
      </option>
    </select>
  </label>
  <fieldset>
    <legend>
      Split equally between
    </legend>
    <label
      class="check"
    >
      <input
        checked=""
        type="checkbox"
      />
      <span>
        Riya
      </span>
    </label>
    <label
      class="check"
    >
      <input
        checked=""
        type="checkbox"
      />
      <span>
        Sam
      </span>
    </label>
  </fieldset>
  <div
    class="row"
  >
    <button>
      Cancel
    </button>
    <button
      class="primary"
    >
      Preview
    </button>
  </div>
</div>
 ❯ waitForWrapper node_modules/@testing-library/dom/dist/wait-for.js:163:27
 ❯ node_modules/@testing-library/dom/dist/query-helpers.js:86:33
 ❯ tests/App.test.tsx:171:26
```

Output tail:

```text
        [0mRiya[0m
      [36m</option>[39m
      [36m<option[39m
        [33mvalue[39m=[32m"12"[39m
      [36m>[39m
        [0mSam[0m
      [36m</option>[39m
    [36m</select>[39m
  [36m</label>[39m
  [36m<fieldset>[39m
    [36m<legend>[39m
      [0mSplit equally between[0m
    [36m</legend>[39m
    [36m<label[39m
      [33mclass[39m=[32m"check"[39m
    [36m>[39m
      [36m<input[39m
        [33mchecked[39m=[32m""[39m
        [33mtype[39m=[32m"checkbox"[39m
      [36m/>[39m
      [36m<span>[39m
        [0mRiya[0m
      [36m</span>[39m
    [36m</label>[39m
    [36m<label[39m
      [33mclass[39m=[32m"check"[39m
    [36m>[39m
      [36m<input[39m
        [33mchecked[39m=[32m""[39m
        [33mtype[39m=[32m"checkbox"[39m
      [36m/>[39m
      [36m<span>[39m
        [0mSam[0m
      [36m</span>[39m
    [36m</label>[39m
  [36m</fieldset>[39m
  [36m<div[39m
    [33mclass[39m=[32m"row"[39m
  [36m>[39m
    [36m<button>[39m
      [0mCancel[0m
    [36m</button>[39m
    [36m<button[39m
      [33mclass[39m=[32m"primary"[39m
    [36m>[39m
      [0mPreview[0m
    [36m</button>[39m
  [36m</div>[39m
[36m</div>[39m
 ❯ waitForWrapper node_modules/@testing-library/dom/dist/wait-for.js:163:27
 ❯ node_modules/@testing-library/dom/dist/query-helpers.js:86:33
 ❯ tests/App.test.tsx:171:26
    169|     await user.click(await screen.findByRole("button", { name: "Split …
    170|     const dialog = await screen.findByRole("dialog");
    171|     await within(dialog).findByText("Riya");
       |                          ^
    172|     await user.click(within(dialog).getByRole("button", { name: "Previ…
    173|     expect(await within(dialog).findByText(/Swiggy · ₹250.00 · split e…

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[1/1]⎯
```
