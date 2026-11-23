# Harness feedback — run `20261123T165748Z_initial-generation`

Overall: **FAIL**. Gates failed: lint-python, typecheck-frontend

Rules for the coding agent (constitution III/IV): fix the implementation. Do NOT edit
tests, specs, thresholds or harness config to make this pass.

## Gate `lint-python` (lint) — exit 1

Output tail:

```text
.harness\run_harness.py:68:12: S314 Using `xml` to parse untrusted data is known to be vulnerable to XML attacks; use `defusedxml` equivalents
.harness\run_harness.py:88:12: S603 `subprocess` call: check for execution of untrusted input
src\splitease\core\splitting.py:64:101: E501 Line too long (101 > 100)
Found 3 errors.
```

## Gate `typecheck-frontend` (lint) — exit 2

Output tail:

```text
src/main.tsx(4,8): error TS2882: Cannot find module or type declarations for side-effect import of './styles.css'.
tests/App.test.tsx(126,13): error TS2322: Type '{ from_member: number; to_member: number; amount: number; }' is not assignable to type 'never'.
tests/App.test.tsx(127,13): error TS2322: Type '{ from_member: number; to_member: number; amount: number; }' is not assignable to type 'never'.
```
