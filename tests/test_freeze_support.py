from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _calls_freeze_support(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == "freeze_support":
                return True
            if isinstance(func, ast.Name) and func.id == "freeze_support":
                return True
    return False


def test_ui_benchmark_calls_freeze_support() -> None:
    assert _calls_freeze_support(ROOT / "bin" / "ui_benchmark.py")


def test_cli_calls_freeze_support() -> None:
    assert _calls_freeze_support(ROOT / "bin" / "cli.py")
