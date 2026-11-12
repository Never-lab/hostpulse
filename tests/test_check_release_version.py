from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_release_version.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_release_version", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_normalize_tag() -> None:
    mod = _load_module()
    assert mod.normalize_tag("v1.4.1") == "1.4.1"
    assert mod.normalize_tag("1.4.1") == "1.4.1"
    assert mod.normalize_tag("V2.0.0") == "2.0.0"


def test_check_passes_for_current_version() -> None:
    mod = _load_module()
    current = mod._version_from_py()
    assert mod.main(["--tag", f"v{current}"]) == 0


def test_check_fails_on_mismatch(capsys: pytest.CaptureFixture[str]) -> None:
    mod = _load_module()
    assert mod.main(["--tag", "v0.0.0-not-a-real-version"]) == 1
    err = capsys.readouterr().err
    assert "mismatch" in err.lower() or "ERROR" in err
