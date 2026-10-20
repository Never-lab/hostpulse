from __future__ import annotations

import json
import sys
from pathlib import Path

BIN = Path(__file__).resolve().parents[1] / "bin"
sys.path.insert(0, str(BIN))

from engine import HostPulseEngine  # noqa: E402
from reporter_generator import ReportGenerator  # noqa: E402


def _write_audit(results_dir: Path, hostname: str, timestamp: int, name: str) -> dict:
    data = {
        "meta": {"hostname": hostname, "timestamp": timestamp, "profile": "generic"},
        "schema_version": 1,
        "engine_version": "1.0.0",
        "sys_info": {},
        "virtualization": {},
        "ram_hw": {},
        "disk_hw": {},
        "health": {"events": []},
        "benchmark": {},
    }
    (results_dir / name).write_text(json.dumps(data), encoding="utf-8")
    return data


def test_get_history_filters_hostname_and_sorts(tmp_path, monkeypatch) -> None:
    engine = HostPulseEngine(quick=True, production_safe=True)
    monkeypatch.setattr(engine, "results_dir", str(tmp_path))

    _write_audit(tmp_path, "host-a", 300, "a_late.json")
    _write_audit(tmp_path, "host-a", 100, "a_early.json")
    _write_audit(tmp_path, "host-b", 200, "b_mid.json")

    only_a = engine.get_history(hostname="host-a")
    assert [h["meta"]["hostname"] for h in only_a] == ["host-a", "host-a"]
    assert [h["meta"]["timestamp"] for h in only_a] == [100, 300]

    all_hosts = engine.get_history()
    assert [h["meta"]["timestamp"] for h in all_hosts] == [100, 200, 300]


def test_compare_build_uses_current_as_main(tmp_path, monkeypatch) -> None:
    """Mirrors orchestrator compare: filter, dedupe ts, append current → main_d."""
    engine = HostPulseEngine(quick=True, production_safe=True)
    monkeypatch.setattr(engine, "results_dir", str(tmp_path))

    _write_audit(tmp_path, "host-a", 100, "old.json")
    _write_audit(tmp_path, "host-b", 150, "other.json")
    _write_audit(tmp_path, "host-a", 999, "stale_same_ts.json")

    current = {
        "meta": {"hostname": "host-a", "timestamp": 999, "profile": "generic"},
        "schema_version": 1,
        "engine_version": "1.4.1",
        "sys_info": {},
        "virtualization": {},
        "ram_hw": {},
        "disk_hw": {},
        "health": {"events": []},
        "benchmark": {},
    }
    engine.data = current

    host = str(engine.data["meta"].get("hostname") or "")
    history = engine.get_history(hostname=host) if host else []
    cur_ts = engine.data["meta"].get("timestamp")
    history = [h for h in history if h.get("meta", {}).get("timestamp") != cur_ts]
    history.append(engine.data)

    assert len(history) == 2
    assert history[-1] is current
    assert history[0]["meta"]["timestamp"] == 100
    assert all(h["meta"]["hostname"] == "host-a" for h in history)

    report = ReportGenerator(history, reference=None, style="corporate")
    assert report.main_d is current
    assert report.main_d["meta"]["timestamp"] == 999

