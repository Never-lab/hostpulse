from __future__ import annotations

import sys
from pathlib import Path
from threading import Event

BIN = Path(__file__).resolve().parents[1] / "bin"
sys.path.insert(0, str(BIN))

from orchestrator import AuditResultPaths, run_audit  # noqa: E402


def test_audit_result_paths_has_score_fields() -> None:
    fields = {f.name for f in AuditResultPaths.__dataclass_fields__.values()}  # type: ignore[attr-defined]
    for name in ("overall_score", "grade", "status", "hostname", "profile", "mode"):
        assert name in fields


def test_run_audit_populates_overall(monkeypatch, tmp_path: Path) -> None:
    """Stub engine + reporter so run_audit returns score without real benchmarks."""
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

        def get_history(self):
            return self.data

    class FakeReporter:
        def __init__(self, *a, **k):
            self.overall = {"score": 88.0, "grade": "A", "status": "ok"}

        def export_presentation_assets(self, d): ...

        def render(self):
            return "<html></html>"

    monkeypatch.setattr(orch, "HostPulseEngine", FakeEngine)
    monkeypatch.setattr(orch, "ReportGenerator", FakeReporter)
    monkeypatch.setattr(orch, "_load_baseline", lambda root: None)

    result = run_audit(
        root_dir=str(tmp_path),
        bin_dir=str(tmp_path),
        profile="db_server",
        quick=True,
        production_safe=True,
        export_slides=False,
        cancel_event=Event(),
    )
    assert result.hostname == "testhost"
    assert result.grade == "A"
    assert result.overall_score == 88.0
    assert result.status == "ok"
    assert result.profile == "db_server"
    assert result.mode == "production-safe"
    assert Path(result.html_path).is_file()
