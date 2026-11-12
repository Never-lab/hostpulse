from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_build_exe_copies_baseline_json() -> None:
    """Windows package must ship config/baseline.json (parity with Linux)."""
    text = (ROOT / "build_exe.ps1").read_text(encoding="utf-8")
    assert "baseline.json" in text
    assert r"config\baseline.json" in text or "config/baseline.json" in text


def test_generate_version_info_writes_file() -> None:
    import subprocess

    subprocess.run(["python3", str(ROOT / "scripts" / "generate_version_info.py")], check=True, cwd=ROOT)
    out = ROOT / "scripts" / "windows_version_info.txt"
    assert out.is_file()
    text = out.read_text(encoding="utf-8")
    assert "VSVersionInfo" in text
    assert "HostPulse" in text
    ver = (ROOT / "bin" / "version.py").read_text(encoding="utf-8")
    m = re.search(r'__version__\s*=\s*"([^"]+)"', ver)
    assert m
    assert m.group(1) in text
