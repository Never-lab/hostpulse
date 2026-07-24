from __future__ import annotations

import ast
from pathlib import Path

import pytest

from cli import main as cli_main


def test_cli_help_exits_ok() -> None:
    with pytest.raises(SystemExit) as exc:
        cli_main(["run", "--help"])
    assert exc.value.code == 0


def test_cli_module_does_not_import_customtkinter() -> None:
    src = Path(__file__).resolve().parents[1] / "bin" / "cli.py"
    tree = ast.parse(src.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    assert "customtkinter" not in imported
    assert not any(name.startswith("customtkinter") for name in imported)
