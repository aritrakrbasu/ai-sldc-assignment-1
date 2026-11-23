"""SplitEase deterministic harness runner (constitution Principle IV).

Runs every mandatory gate defined in ``.harness/gates.json`` as an independent subprocess,
records raw stdout/stderr, exit code and duration per gate, extracts failing tests from JUnit
XML, and writes a machine-readable ``result.json`` plus a ``feedback.md`` that is handed to the
coding agent when anything fails.

Usage:
    python .harness/run_harness.py --label <short-name>
    python .harness/run_harness.py --relock --reason "<why the harness config changed>"

Exit code: 0 when every gate passes, 1 otherwise.

Integrity: the hash of the harness configuration files is pinned in ``.harness/gates.lock``.
If the configuration changes without an explicit, logged ``--relock`` the run is refused, so
gates cannot be silently weakened to obtain a PASS.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import subprocess  # nosec B404 - the harness exists to run fixed, configured tool commands
import sys
import time
from pathlib import Path

from defusedxml import ElementTree as ET  # safe XML parsing (ruff S314 / bandit B314)

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / ".harness"
EVIDENCE = ROOT / "evidence" / "harness-runs"
LOCK_FILE = HARNESS / "gates.lock"
RELOCK_LOG = HARNESS / "relock-log.md"
PINNED_FILES = [
    ".harness/gates.json",
    ".harness/ruff.toml",
    ".harness/bandit.yaml",
    ".harness/run_harness.py",
    "frontend/eslint.config.js",
    "pyproject.toml",
]
MAX_LOG_TAIL = 60


def config_hash() -> str:
    digest = hashlib.sha256()
    for rel in PINNED_FILES:
        path = ROOT / rel
        digest.update(rel.encode())
        digest.update(path.read_bytes().replace(b"\r\n", b"\n") if path.exists() else b"<missing>")
    return digest.hexdigest()


def resolve_tool(name: str) -> str:
    found = shutil.which(name + ".cmd") or shutil.which(name)
    if not found:
        raise SystemExit(f"harness: required tool '{name}' not found on PATH")
    return found


def junit_failures(xml_path: Path) -> list[dict[str, str]]:
    if not xml_path.exists():
        return []
    failures: list[dict[str, str]] = []
    tree = ET.parse(xml_path)
    for case in tree.iter("testcase"):
        for tag in ("failure", "error"):
            node = case.find(tag)
            if node is not None:
                failures.append(
                    {
                        "test": f"{case.get('classname', '')}::{case.get('name', '')}",
                        "kind": tag,
                        "message": (node.get("message") or "").strip()[:500],
                        "detail": (node.text or "").strip()[-1500:],
                    }
                )
    return failures


def run_gate(gate: dict, run_dir: Path, tools: dict[str, str]) -> dict:
    subst = {**tools, "run_dir": str(run_dir)}
    cmd = [part.format(**subst) for part in gate["cmd"]]
    started = time.perf_counter()
    # The harness exists to run the fixed tool commands pinned (hash-locked) in gates.json.
    proc = subprocess.run(  # noqa: S603  # nosec B603
        cmd,
        cwd=ROOT / gate["cwd"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    duration = round(time.perf_counter() - started, 2)
    log_path = run_dir / f"{gate['id']}.log"
    log_path.write_text(
        f"$ {' '.join(cmd)}\n(cwd={gate['cwd']}, exit={proc.returncode}, {duration}s)\n\n"
        f"--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}\n",
        encoding="utf-8",
    )
    result = {
        "id": gate["id"],
        "kind": gate["kind"],
        "status": "PASS" if proc.returncode == 0 else "FAIL",
        "exit_code": proc.returncode,
        "duration_s": duration,
        "command": cmd,
        "log": log_path.name,
        "failures": [],
    }
    if result["status"] == "FAIL":
        if gate.get("junit"):
            result["failures"] = junit_failures(run_dir / gate["junit"])
        tail = (proc.stdout + "\n" + proc.stderr).strip().splitlines()[-MAX_LOG_TAIL:]
        result["output_tail"] = tail
    return result


def write_feedback(run_dir: Path, summary: dict) -> None:
    lines = [
        f"# Harness feedback — run `{summary['run_id']}`",
        "",
        f"Overall: **{summary['overall']}**. Gates failed: "
        + (", ".join(g["id"] for g in summary["gates"] if g["status"] == "FAIL") or "none"),
        "",
        "Rules for the coding agent (constitution III/IV): fix the implementation. Do NOT edit",
        "tests, specs, thresholds or harness config to make this pass.",
        "",
    ]
    for gate in summary["gates"]:
        if gate["status"] == "PASS":
            continue
        lines += [f"## Gate `{gate['id']}` ({gate['kind']}) — exit {gate['exit_code']}", ""]
        for failure in gate["failures"]:
            lines += [
                f"### Failing test `{failure['test']}`",
                f"- Observed ({failure['kind']}): {failure['message']}",
                "",
                "```text",
                failure["detail"],
                "```",
                "",
            ]
        lines += ["Output tail:", "", "```text", *gate.get("output_tail", []), "```", ""]
    (run_dir / "feedback.md").write_text("\n".join(lines), encoding="utf-8")


def relock(reason: str) -> int:
    if not reason.strip():
        raise SystemExit("--relock requires --reason")
    new_hash = config_hash()
    old_hash = LOCK_FILE.read_text().strip() if LOCK_FILE.exists() else "<none>"
    LOCK_FILE.write_text(new_hash + "\n")
    stamp = dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    with RELOCK_LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"- {stamp}: {old_hash[:12]} -> {new_hash[:12]} — {reason}\n")
    print(f"harness config relocked: {new_hash[:12]}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--label", default="run")
    parser.add_argument("--relock", action="store_true")
    parser.add_argument("--reason", default="")
    args = parser.parse_args()
    if args.relock:
        return relock(args.reason)

    expected = LOCK_FILE.read_text().strip() if LOCK_FILE.exists() else None
    actual = config_hash()
    if expected != actual:
        print(
            "harness: REFUSED — harness configuration changed since it was locked.\n"
            f"  expected {expected}\n  actual   {actual}\n"
            "Re-lock only with an explicit, logged reason: --relock --reason '...'",
            file=sys.stderr,
        )
        return 2

    gates = json.loads((HARNESS / "gates.json").read_text(encoding="utf-8"))["gates"]
    tools = {"python": sys.executable, "npm": resolve_tool("npm"), "npx": resolve_tool("npx")}
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{stamp}_{args.label}"
    run_dir = EVIDENCE / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    results = []
    for gate in gates:
        print(f"[harness] {gate['id']:<20} ...", end="", flush=True)
        res = run_gate(gate, run_dir, tools)
        print(f" {res['status']}  ({res['duration_s']}s)")
        results.append(res)

    overall = "PASS" if all(r["status"] == "PASS" for r in results) else "FAIL"
    summary = {
        "run_id": run_id,
        "label": args.label,
        "timestamp_utc": stamp,
        "config_hash": actual,
        "python": sys.version.split()[0],
        "overall": overall,
        "gates": results,
    }
    (run_dir / "result.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_feedback(run_dir, summary)
    with (EVIDENCE / "index.md").open("a", encoding="utf-8") as fh:
        gate_cells = " ".join(f"{r['id']}={r['status']}" for r in results)
        fh.write(f"| {run_id} | {overall} | {gate_cells} |\n")
    print(f"[harness] OVERALL {overall} — evidence: {run_dir.relative_to(ROOT)}")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
