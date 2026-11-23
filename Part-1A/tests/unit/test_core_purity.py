"""T009 — constitution Principle II: the domain core performs no I/O, clock reads or randomness."""

import ast
from pathlib import Path

import splitease.core as core_pkg

FORBIDDEN_MODULES = {"sqlite3", "fastapi", "random", "time", "os", "socket", "subprocess",
                     "requests", "httpx", "secrets", "uuid"}
FORBIDDEN_CALLS = {"now", "today", "utcnow", "open", "print", "input"}


def _core_files():
    return sorted(Path(core_pkg.__file__).parent.glob("*.py"))


def test_core_has_modules():
    names = {p.stem for p in _core_files()}
    assert {"errors", "money", "model", "groups", "splitting", "balances", "settle",
            "settlements", "ledger_csv"} <= names


def test_core_imports_no_io_or_randomness():
    for path in _core_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom):
                roots = {(node.module or "").split(".")[0]}
            else:
                continue
            assert not roots & FORBIDDEN_MODULES, f"{path.name} imports {roots & FORBIDDEN_MODULES}"
            module = getattr(node, "module", None) or ""
            assert not module.startswith(("splitease.api", "splitease.storage")), path.name


def test_core_calls_no_clock_or_io():
    for path in _core_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func
                name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
                assert name not in FORBIDDEN_CALLS, f"{path.name} calls {name}()"


def test_core_uses_no_float_literals():
    """Constitution I: no floating point in money code."""
    for path in _core_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant):
                assert not isinstance(node.value, float), f"float literal in {path.name}"
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "float":
                raise AssertionError(f"float() call in {path.name}")
