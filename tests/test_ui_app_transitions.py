from __future__ import annotations

import sys
from pathlib import Path

BIN = Path(__file__).resolve().parents[1] / "bin"
sys.path.insert(0, str(BIN))

from ui.app import ShellController  # noqa: E402


def test_controller_flow() -> None:
    c = ShellController()
    assert c.state == "setup"
    c.begin_run()
    assert c.state == "live"
    c.finish_run()
    assert c.state == "done"
    c.cancel_to_setup()
    assert c.state == "setup"


def test_controller_cancel_from_live() -> None:
    c = ShellController()
    c.begin_run()
    assert c.state == "live"
    c.cancel_to_setup()
    assert c.state == "setup"
