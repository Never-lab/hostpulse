from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_build_exe_copies_baseline_json() -> None:
    """Windows package must ship config/baseline.json (parity with Linux)."""
    text = (ROOT / "build_exe.ps1").read_text(encoding="utf-8")
    assert "baseline.json" in text
    assert r"config\baseline.json" in text or "config/baseline.json" in text


def test_verify_local_asserts_onedir_internal() -> None:
    text = (ROOT / "scripts" / "verify_local.ps1").read_text(encoding="utf-8")
    assert "_internal" in text
    assert "onedir" in text.lower()


def test_release_workflow_publishes_sha256sums() -> None:
    text = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert "SHA256SUMS.txt" in text
    assert "sha256sum" in text


def test_docker_cross_build_marked_deprecated() -> None:
    text = (ROOT / "build_exe_windows.py").read_text(encoding="utf-8")
    assert "DEPRECATED" in text


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
