#!/usr/bin/env python3
"""Generate PyInstaller Windows version resource from bin/version.py."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "scripts" / "windows_version_info.txt"


def _parse_version(text: str) -> tuple[int, int, int, int]:
    m = re.search(r'__version__\s*=\s*"([^"]+)"', text)
    if not m:
        raise SystemExit("version missing in bin/version.py")
    parts = [int(p) for p in m.group(1).split(".")]
    while len(parts) < 4:
        parts.append(0)
    return tuple(parts[:4])  # type: ignore[return-value]


def main() -> int:
    ver_text = (ROOT / "bin" / "version.py").read_text(encoding="utf-8")
    filevers = _parse_version(ver_text)
    ver_str = ".".join(str(p) for p in filevers[:3])
    content = f"""# UTF-8
# Auto-generated — do not edit by hand.
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={filevers},
    prodvers={filevers},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [StringStruct('CompanyName', 'Never-lab'),
        StringStruct('FileDescription', 'HostPulse hardware/OS benchmark'),
        StringStruct('FileVersion', '{ver_str}'),
        StringStruct('InternalName', 'HostPulse'),
        StringStruct('LegalCopyright', 'MIT License'),
        StringStruct('OriginalFilename', 'HostPulse.exe'),
        StringStruct('ProductName', 'HostPulse'),
        StringStruct('ProductVersion', '{ver_str}')])
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
    OUT.write_text(content, encoding="utf-8")
    print(f"Wrote {OUT} ({ver_str})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
