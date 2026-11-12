from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import MagicMock

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


def _fake_audit_result() -> MagicMock:
    html = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "minimal_audit.json"
    return MagicMock(html_path=str(html))


def test_cli_db_without_prod_safe_refuses(monkeypatch, capsys) -> None:
    fake = MagicMock(return_value=_fake_audit_result())
    monkeypatch.setattr("cli.run_audit", fake)
    code = cli_main(["run", "--profile", "db_server"])
    assert code == 2
    err = capsys.readouterr().err
    assert "Refusing full-load" in err
    assert fake.call_count == 0


def test_cli_db_with_force_proceeds(monkeypatch, capsys) -> None:
    fake = MagicMock(return_value=_fake_audit_result())
    monkeypatch.setattr("cli.run_audit", fake)
    code = cli_main(["run", "--profile", "db_server", "--force"])
    assert code == 0
    assert fake.call_count == 1
    err = capsys.readouterr().err
    assert "--force" in err


def test_cli_db_production_safe_proceeds(monkeypatch) -> None:
    fake = MagicMock(return_value=_fake_audit_result())
    monkeypatch.setattr("cli.run_audit", fake)
    code = cli_main(["run", "--profile", "app_server", "--production-safe"])
    assert code == 0
    assert fake.call_count == 1
