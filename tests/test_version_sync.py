from __future__ import annotations

import re
from pathlib import Path

from version import __version__

ROOT = Path(__file__).resolve().parents[1]


def test_version_matches_pyproject() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
    assert m, "version missing in pyproject.toml"
    assert __version__ == m.group(1)
