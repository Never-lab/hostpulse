from __future__ import annotations

import sys
from pathlib import Path

BIN = Path(__file__).resolve().parents[1] / "bin"
sys.path.insert(0, str(BIN))

from ui.theme import COLORS, status_color  # noqa: E402


def test_colors_match_report_palette() -> None:
    assert COLORS["bg"] == "#0f172a"
    assert COLORS["accent"] == "#0284c7"
    assert COLORS["brand"] == "#0c4a6e"
    assert COLORS["ok"] == "#16a34a"
    assert COLORS["warn"] == "#d97706"
    assert COLORS["crit"] == "#dc2626"


def test_status_color_maps() -> None:
    assert status_color("ok") == COLORS["ok"]
    assert status_color("warn") == COLORS["warn"]
    assert status_color("crit") == COLORS["crit"]
    assert status_color("na") == COLORS["muted"]
    assert status_color("unknown") == COLORS["muted"]
