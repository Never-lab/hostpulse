"""#49 — slides export off by default; CLI opts in explicitly."""

from __future__ import annotations

import inspect
import sys
from pathlib import Path
from unittest.mock import MagicMock

BIN = Path(__file__).resolve().parents[1] / "bin"
sys.path.insert(0, str(BIN))

from cli import _build_parser  # noqa: E402
from orchestrator import run_audit  # noqa: E402


def test_run_audit_export_slides_defaults_false() -> None:
    default = inspect.signature(run_audit).parameters["export_slides"].default
    assert default is False


def test_cli_slides_opt_in_defaults_false() -> None:
    args = _build_parser().parse_args(["run"])
    assert args.slides is False


def test_cli_slides_flag_enables_export() -> None:
    args = _build_parser().parse_args(["run", "--slides"])
    assert args.slides is True


def test_cli_deprecated_no_slides_still_parses() -> None:
    args = _build_parser().parse_args(["run", "--no-slides"])
    assert args.slides is False
    assert args.no_slides is True


def test_run_audit_skips_slide_export_when_default(monkeypatch, tmp_path: Path) -> None:
    import orchestrator as orch

    class FakeEngine:
        def __init__(self, **kwargs):
            self.cancel_event = None
            self.skip_chaos = True
            self.config = {}
            self.data = {
                "meta": {"hostname": "testhost", "is_admin": False},
                "benchmark": {"chaos": {}},
            }

        def collect_sys_info(self): ...
        def cpu_benchmark_suite(self): ...
        def cpu_real_world(self): ...
        def ram_benchmark(self): ...
        def net_benchmark(self): ...
        def disk_benchmarks(self): ...
        def chaos_disk_under_load(self): ...

        def save_results(self):
            return str(tmp_path / "out.json")

        def get_history(self, hostname=None):
            return []

    fake_reporter = MagicMock()
    fake_reporter.render.return_value = "<html/>"
    fake_reporter.overall = {"score": 1.0, "grade": "A", "status": "ok"}

    monkeypatch.setattr(orch, "HostPulseEngine", FakeEngine)
    monkeypatch.setattr(orch, "ReportGenerator", lambda *a, **k: fake_reporter)
    monkeypatch.setattr(orch, "_load_baseline", lambda root: None)

    orch.run_audit(root_dir=str(tmp_path), bin_dir=str(tmp_path), quick=True, production_safe=True)

    fake_reporter.export_presentation_assets.assert_not_called()
