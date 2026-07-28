from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
