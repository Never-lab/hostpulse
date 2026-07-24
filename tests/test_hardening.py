"""Hardening: mktemp removal, deps message, production-safe warn (#3 #4 #8)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "bin"
if str(BIN) not in sys.path:
    sys.path.insert(0, str(BIN))


def test_engine_does_not_use_mktemp() -> None:
    src = (BIN / "engine.py").read_text(encoding="utf-8")
    assert "mktemp" not in src
    assert "NamedTemporaryFile" in src


def test_ui_does_not_auto_pip() -> None:
    src = (BIN / "ui_benchmark.py").read_text(encoding="utf-8")
    assert "pip install" not in src.lower()
    assert "require_dependencies" in src
    assert "_ensure_dependencies" not in src


def test_missing_packages_empty_when_present() -> None:
    from deps_check import missing_packages

    assert missing_packages(["sys"]) == []


def test_missing_packages_reports_absent() -> None:
    from deps_check import missing_packages

    assert missing_packages(["definitely_not_a_real_pkg_xyz"]) == [
        "definitely_not_a_real_pkg_xyz"
    ]


def test_require_dependencies_frozen_skips() -> None:
    from deps_check import require_dependencies

    require_dependencies(frozen=True)  # must not raise


def test_require_dependencies_raises_on_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    import deps_check

    monkeypatch.setattr(deps_check, "missing_packages", lambda packages=None: ["psutil"])
    with pytest.raises(SystemExit) as exc:
        deps_check.require_dependencies(frozen=False)
    assert "psutil" in str(exc.value)
    assert "pip install -r requirements.txt" in str(exc.value)


@pytest.mark.parametrize(
    ("profile", "safe", "expect"),
    [
        ("generic", False, False),
        ("app_server", True, False),
        ("app_server", False, True),
        ("db_server", False, True),
        ("db_server", True, False),
    ],
)
def test_needs_full_load_confirm(profile: str, safe: bool, expect: bool) -> None:
    from load_safety import needs_full_load_confirm

    assert needs_full_load_confirm(profile, safe) is expect
