"""MoneyLens single evaluation harness (spec FR-020, constitution IV, research R7).

Pipeline per case and repeat:
    dataset case -> MoneyLens HTTP API (in-process, real Gemini client) -> generated output
    -> Layer 1 structural (JSON Schema) -> Layer 2 properties/invariants -> Layer 3 semantic score
Then aggregate against evals/threshold.json -> PASS / FAIL / INCONCLUSIVE (or SMOKE when run
with fewer repeats than declared). Writes evidence/eval-runs/<ts>_<label>/.

Usage:
    python .harness/evaluate.py --label <name> [--cases P01,A03] [--repeats N] [--no-timing]
    python .harness/evaluate.py --relock --reason "<why dataset/threshold/checks changed>"
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".harness"))
sys.path.insert(0, str(ROOT / "src"))

from checks import properties, semantic, structural  # noqa: E402

DATASET = ROOT / "evals" / "dataset.json"
THRESHOLD = ROOT / "evals" / "threshold.json"
RUNS = ROOT / "evidence" / "eval-runs"
LOCK = ROOT / ".harness" / "eval.lock"
RELOCK_LOG = ROOT / ".harness" / "relock-log.md"
LOCKED = ["evals/dataset.json", "evals/threshold.json", "evals/fixtures/transactions.json",
          ".harness/evaluate.py", ".harness/checks/structural.py",
          ".harness/checks/properties.py", ".harness/checks/semantic.py",
          "specs/001-sms-finance-inbox/contracts/parse_result.schema.json",
          "specs/001-sms-finance-inbox/contracts/query_result.schema.json"]
SERVICE_CODES = {"MODEL_UNAVAILABLE"}


def lock_hash() -> str:
    h = hashlib.sha256()
    for rel in LOCKED:
        h.update(rel.encode())
        h.update((ROOT / rel).read_bytes().replace(b"\r\n", b"\n"))
    return h.hexdigest()


class RecordingLLM:
    """Wraps the application's LLM client and records every prompt that leaves the process,
    so INV-6 can verify that nothing secret is sent to the model."""

    def __init__(self, inner):
        self.inner = inner
        self.sent: list[str] = []

    def __getattr__(self, name):
        return getattr(self.inner, name)

    def generate_json(self, system: str, user: str, schema: dict) -> str:
        self.sent.append(system + "\n" + user)
        return self.inner.generate_json(system, user, schema)


def make_client(db_path: str, llm):
    from fastapi.testclient import TestClient

    from moneylens.api.app import create_app
    return TestClient(create_app(db_path=db_path, llm=llm))


def run_parse(case: dict, llm: RecordingLLM, tmp: Path) -> tuple[dict, list[str]]:
    llm.sent = []
    with make_client(str(tmp / "parse.sqlite3"), llm) as client:
        resp = client.post("/api/parse", json={"messages": case["input"]["messages"],
                                               "reference_date": case["reference_date"],
                                               "save": False})
    body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") \
        else {"raw": resp.text}
    body["_http_status"] = resp.status_code
    return body, list(llm.sent)


def run_ask(case: dict, llm: RecordingLLM, tmp: Path, fixture: dict) -> dict:
    from moneylens.storage.repository import Repository
    db = tmp / f"ask-{case['id']}.sqlite3"
    if db.exists():
        db.unlink()
    repo = Repository(str(db))
    for t in fixture["transactions"]:
        repo.add_transaction_record(t, fixture["reference_date"])
    repo.close()
    llm.sent = []
    with make_client(str(db), llm) as client:
        resp = client.post("/api/ask", json={"question": case["input"]["question"],
                                             "reference_date": case["reference_date"]})
    body = resp.json()
    body["_http_status"] = resp.status_code
    return body


def is_service_error(case: dict, body: dict) -> bool:
    if case["type"] == "ask":
        return body.get("error_code") in SERVICE_CODES
    return any(r.get("error_code") in SERVICE_CODES for r in body.get("results", []))


def evaluate_repeat(case, body, prompts, fixture, weights):
    clean = {k: v for k, v in body.items() if not k.startswith("_")}
    if body.get("_http_status") != 200:
        l1 = [f"HTTP {body.get('_http_status')}"]
    elif case["type"] == "parse":
        l1 = structural.check_parse_response(clean, len(case["input"]["messages"]))
    else:
        l1 = structural.check_ask_response(clean)
    if case["type"] == "parse":
        l2 = properties.check_parse_case(case, clean, prompts) if not l1 else []
        score, detail = semantic.score_parse_case(case, clean, weights)
    else:
        l2 = properties.check_ask_case(case, clean, fixture["transactions"]) if not l1 else []
        score, detail = semantic.score_ask_case(case, clean, weights)
    if l1:
        score = 0.0
    return {"layer1": l1, "layer2": l2, "semantic": score, "semantic_detail": detail,
            "output": clean}


def scan_evidence(run_dir: Path, secrets: set[str], outputs: list[dict]) -> list[str]:
    """INV-6 on evidence: exact dataset secrets anywhere in any written file, and FR-002(b)
    long numbers inside the recorded application outputs (hashes/timestamps are not outputs)."""
    pattern = re.compile(r"(?<!\d)(?:\d{9,}|\d{4}(?:[ -]\d{4}){2,3})(?!\d)")
    leaks = []
    for path in run_dir.glob("*"):
        text = path.read_text(encoding="utf-8")
        leaks += [f"{path.name}: secret '{s[:2]}…'" for s in secrets if s and s in text]
    for m in pattern.finditer(json.dumps(outputs, ensure_ascii=False)):
        leaks.append(f"outputs: long digit run ({len(m.group())} chars)")
    return leaks


def sc004_timing(llm, cases, batch_size, tmp) -> dict:
    msgs = [m for c in cases if c["type"] == "parse" for m in c["input"]["messages"]
            if m.strip() and len(m) <= 1000][:batch_size]
    start = time.perf_counter()
    with make_client(str(tmp / "timing.sqlite3"), llm) as client:
        resp = client.post("/api/parse", json={"messages": msgs, "reference_date": "2026-11-23",
                                               "save": False})
    seconds = round(time.perf_counter() - start, 2)
    errors = sum(1 for r in resp.json().get("results", []) if r.get("status") == "error")
    return {"messages": len(msgs), "seconds": seconds, "http": resp.status_code,
            "error_results": errors}


def write_failures(run_dir: Path, summary: dict, per_case: list[dict]) -> None:
    lines = [f"# Evaluation failures — `{summary['run_id']}`", "",
             f"Decision: **{summary['decision']}**", "",
             "Rules for the coding agent (constitution IV): repair application code, prompts,",
             "parsers, validators or guardrails. Do NOT edit dataset cases, expected results,",
             "threshold or harness checks to obtain PASS.", ""]
    for c in per_case:
        if c["status"] == "PASS":
            continue
        lines += [f"## {c['id']} — {c['status']} ({', '.join(c['tags'])})",
                  f"Requirement refs: {', '.join(c['requirement_refs'])}. {c['description']}", ""]
        for i, r in enumerate(c["repeats"]):
            if r.get("service_error"):
                lines.append(f"- repeat {i + 1}: SERVICE_ERROR (excluded)")
                continue
            lines.append(f"- repeat {i + 1}: semantic={r['semantic']} "
                         f"L1={r['layer1'] or 'ok'} L2={r['layer2'] or 'ok'}")
            lines.append(f"  - field scores: `{json.dumps(r['semantic_detail'])}`")
        last = next((r for r in reversed(c["repeats"]) if not r.get("service_error")), None)
        if last:
            lines += ["", "Expected:", "```json", json.dumps(c["expected"], indent=1), "```",
                      "Observed (last non-service repeat):", "```json",
                      json.dumps(last["output"], indent=1, ensure_ascii=False)[:3000], "```", ""]
    (run_dir / "failures.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default="eval")
    ap.add_argument("--cases", default="")
    ap.add_argument("--repeats", type=int, default=None)
    ap.add_argument("--no-timing", action="store_true")
    ap.add_argument("--relock", action="store_true")
    ap.add_argument("--reason", default="")
    args = ap.parse_args()

    if args.relock:
        if not args.reason.strip():
            raise SystemExit("--relock requires --reason")
        old = LOCK.read_text().strip() if LOCK.exists() else "<none>"
        new = lock_hash()
        LOCK.write_text(new + "\n")
        stamp = dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        with RELOCK_LOG.open("a", encoding="utf-8") as fh:
            fh.write(f"- {stamp} [eval.lock]: {old[:12]} -> {new[:12]} — {args.reason}\n")
        print("eval lock updated:", new[:12])
        return 0
    if not LOCK.exists() or LOCK.read_text().strip() != lock_hash():
        print("evaluate: REFUSED — dataset/threshold/checks changed since lock. "
              "Use --relock --reason '...'", file=sys.stderr)
        return 2

    from moneylens.ai.llm import GeminiClient
    from moneylens.config import load_settings
    settings = load_settings()
    if not settings.key_configured or not settings.model:
        print("evaluate: GEMINI_API_KEY and MONEYLENS_MODEL must be set (see README).",
              file=sys.stderr)
        return 3

    threshold = json.loads(THRESHOLD.read_text(encoding="utf-8"))
    dataset = json.loads(DATASET.read_text(encoding="utf-8"))
    cases = dataset["cases"]
    if args.cases:
        wanted = set(args.cases.split(","))
        cases = [c for c in cases if c["id"] in wanted]
    repeats = args.repeats or threshold["repeats"]
    smoke = repeats < threshold["repeats"] or bool(args.cases)
    fixture = json.loads((ROOT / "evals/fixtures/transactions.json").read_text(encoding="utf-8"))
    llm = RecordingLLM(GeminiClient.from_settings(settings))

    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{stamp}_{args.label}"
    run_dir = RUNS / run_id
    run_dir.mkdir(parents=True)
    per_case, calls, service = [], 0, 0
    with tempfile.TemporaryDirectory() as tmpd:
        tmp = Path(tmpd)
        for case in cases:
            reps = []
            for r in range(repeats):
                if case["type"] == "parse":
                    body, prompts = run_parse(case, llm, tmp)
                else:
                    body, prompts = run_ask(case, llm, tmp, fixture), []
                calls += 1
                if is_service_error(case, body):
                    service += 1
                    reps.append({"service_error": True})
                    print(f"  {case['id']} r{r + 1}: SERVICE_ERROR")
                    continue
                res = evaluate_repeat(case, body, prompts, fixture, threshold["weights"])
                res["pass"] = (not res["layer1"] and not res["layer2"]
                               and res["semantic"] >= threshold["case_semantic_min"])
                reps.append(res)
                print(f"  {case['id']} r{r + 1}: {'pass' if res['pass'] else 'FAIL'} "
                      f"sem={res['semantic']} L1={len(res['layer1'])} L2={len(res['layer2'])}")
            scored = [x for x in reps if not x.get("service_error")]
            status = ("SERVICE_ERROR" if not scored else
                      "PASS" if all(x["pass"] for x in scored) else "FAIL")
            per_case.append({"id": case["id"], "type": case["type"], "tags": case["tags"],
                             "requirement_refs": case["requirement_refs"],
                             "description": case["description"], "expected": case["expected"],
                             "status": status, "repeats": reps})
        timing = None if args.no_timing else sc004_timing(
            llm, dataset["cases"], threshold["sc004_batch_size"], tmp)

    scored_cases = [c for c in per_case if c["status"] != "SERVICE_ERROR"]
    scored_reps = [r for c in scored_cases for r in c["repeats"] if not r.get("service_error")]
    guard = [c for c in scored_cases if "guardrail" in c["tags"]]
    metrics = {
        "cases_total": len(per_case),
        "cases_scored": len(scored_cases),
        "repeats_scored": len(scored_reps),
        "model_calls_attempted": calls,
        "service_errors": service,
        "service_error_ratio": round(service / calls, 4) if calls else 0.0,
        "structural_pass_rate": round(sum(not r["layer1"] for r in scored_reps)
                                      / len(scored_reps), 4) if scored_reps else 0.0,
        "property_pass_rate": round(sum(not r["layer2"] for r in scored_reps)
                                    / len(scored_reps), 4) if scored_reps else 0.0,
        "guardrail_case_pass_rate": round(sum(c["status"] == "PASS" for c in guard)
                                          / len(guard), 4) if guard else 1.0,
        "case_pass_rate": round(sum(c["status"] == "PASS" for c in scored_cases)
                                / len(scored_cases), 4) if scored_cases else 0.0,
        "mean_semantic": round(sum(r["semantic"] for r in scored_reps) / len(scored_reps), 4)
        if scored_reps else 0.0,
    }
    agg = threshold["aggregate"]
    conditions = {
        "a_structural": metrics["structural_pass_rate"] >= agg["structural_pass_rate_min"],
        "b_guardrail": metrics["guardrail_case_pass_rate"] >= agg["guardrail_case_pass_rate_min"],
        "c_case_pass_rate": metrics["case_pass_rate"] >= agg["case_pass_rate_min"],
        "d_mean_semantic": metrics["mean_semantic"] >= agg["mean_semantic_min"],
    }
    if metrics["service_error_ratio"] > threshold["service_error_ratio_max"]:
        decision = "INCONCLUSIVE"
    elif smoke:
        decision = "SMOKE_" + ("PASS" if all(conditions.values()) else "FAIL")
    else:
        decision = "PASS" if all(conditions.values()) else "FAIL"

    summary = {
        "run_id": run_id, "label": args.label, "timestamp_utc": stamp, "decision": decision,
        "smoke": smoke, "repeats": repeats,
        "model": {"model": llm.model, "model_version": getattr(llm, "model_version", None),
                  "temperature": llm.temperature, "prompt_versions": llm_prompt_versions()},
        "threshold": threshold, "conditions": conditions, "metrics": metrics,
        "sc004_timing": timing, "eval_lock": lock_hash(), "cases": per_case,
    }
    (run_dir / "eval-results.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False),
                                               encoding="utf-8")
    write_failures(run_dir, summary, per_case)
    secrets = {s for c in dataset["cases"] for s in c.get("secrets", [])}
    outputs = [r["output"] for c in per_case for r in c["repeats"] if "output" in r]
    leaks = scan_evidence(run_dir, secrets, outputs)
    if leaks:
        summary["decision"] = "FAIL"
        summary["evidence_leak"] = leaks
        (run_dir / "eval-results.json").write_text(
            json.dumps({"run_id": run_id, "decision": "FAIL", "error": "EVIDENCE_LEAK",
                        "count": len(leaks)}, indent=2), encoding="utf-8")
        (run_dir / "failures.md").write_text("# EVIDENCE_LEAK\n\nEvidence files contained "
                                             f"{len(leaks)} secret/long-number matches; "
                                             "outputs were withheld.\n", encoding="utf-8")
    with (RUNS / "index.md").open("a", encoding="utf-8") as fh:
        fh.write(f"| {run_id} | {summary['decision']} | {metrics['case_pass_rate']} | "
                 f"{metrics['mean_semantic']} | {metrics['guardrail_case_pass_rate']} | "
                 f"{metrics['structural_pass_rate']} | {metrics['service_error_ratio']} |\n")
    print(json.dumps({"decision": summary["decision"], "conditions": conditions,
                      "metrics": metrics, "sc004": timing}, indent=2))
    print("evidence:", run_dir.relative_to(ROOT))
    return 0 if summary["decision"] in ("PASS", "SMOKE_PASS") else 1


def llm_prompt_versions() -> dict:
    from moneylens.ai.parser import PROMPT_VERSION as parse_v
    from moneylens.ai.qa import PROMPT_VERSION as query_v
    return {"parse": parse_v, "query": query_v}


if __name__ == "__main__":
    sys.exit(main())
