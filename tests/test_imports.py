from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "bin"


@pytest.fixture(scope="module", autouse=True)
def _ensure_bin_on_path() -> None:
    path = str(BIN)
    if path not in sys.path:
        sys.path.insert(0, path)


@pytest.mark.parametrize(
    "modname",
    ["app_paths", "version", "schema", "cancel", "orchestrator", "pdf_export", "engine", "reporter_generator", "cli", "ui", "ui.theme", "ui.presets", "ui.app"],
)
def test_import_core_modules(modname: str) -> None:
    mod = importlib.import_module(modname)
    assert mod is not None


def test_import_ui_benchmark_windows_only() -> None:
    if sys.platform != "win32":
        pytest.skip("GUI import smoke is Windows-focused (Tk/CustomTkinter)")
    mod = importlib.import_module("ui_benchmark")
    assert hasattr(mod, "AuditApp")
    assert hasattr(mod, "main")
