from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from engine import HostPulseEngine
from schema import REQUIRED_CHAOS_KEYS, REQUIRED_DISK_KEYS


def test_disk_benchmarks_writes_keys_quick_tmp(tmp_path) -> None:
    engine = HostPulseEngine(quick=True, production_safe=False)
    engine.config["DISK_SEQ_MB"] = 1
    engine.config["DISK_IOPS_ITERATIONS"] = 50
    engine.config["DISK_TEST_PATH"] = str(tmp_path)

    engine.disk_benchmarks()

    disk = engine.data["benchmark"]["disk"]
    for key in REQUIRED_DISK_KEYS:
        assert key in disk
    assert disk["seq_write_mb"] > 0
    assert disk["seq_read_mb"] > 0
    assert disk["iops"] >= 0


def test_disk_benchmarks_skips_when_free_space_too_low(tmp_path, monkeypatch) -> None:
    engine = HostPulseEngine(quick=True, production_safe=False)
    engine.config["DISK_SEQ_MB"] = 128
    engine.config["DISK_IOPS_ITERATIONS"] = 50
    engine.config["DISK_TEST_PATH"] = str(tmp_path)

    monkeypatch.setattr(
        "engine.psutil.disk_usage",
        lambda _p: SimpleNamespace(free=8 * 1024 * 1024),
    )

    engine.disk_benchmarks()

    disk = engine.data["benchmark"]["disk"]
    assert disk["seq_write_mb"] == 0
    assert disk["seq_read_mb"] == 0
    codes = [e["code"] for e in engine.data["health"]["events"]]
    assert "DISK_INSUFFICIENT_SPACE" in codes


def test_chaos_skip_production_safe_preserves_json_keys() -> None:
    engine = HostPulseEngine(quick=True, production_safe=True)
    assert engine.skip_chaos is True

    engine.chaos_disk_under_load()

    chaos = engine.data["benchmark"]["chaos"]
    for key in REQUIRED_CHAOS_KEYS:
        assert key in chaos
    assert chaos["active"] is False
    assert chaos["disk_iops_under_load"] == 0
    assert chaos["impact_pct"] == 0


def test_chaos_disk_under_load_mocked(monkeypatch) -> None:
    engine = HostPulseEngine(quick=True, production_safe=False)
    engine.skip_chaos = False

    calls = {"n": 0}

    def fake_iops(iterations, seq_mb):
        calls["n"] += 1
        return 1000.0 if calls["n"] == 1 else 500.0

    fake_proc = MagicMock()
    fake_proc.is_alive.return_value = False

    monkeypatch.setattr("engine._measure_disk_iops", fake_iops)
    monkeypatch.setattr("engine.multiprocessing.Process", MagicMock(return_value=fake_proc))

    engine.chaos_disk_under_load()

    chaos = engine.data["benchmark"]["chaos"]
    for key in REQUIRED_CHAOS_KEYS:
        assert key in chaos
    assert chaos["active"] is True
    assert chaos["disk_iops_under_load"] == 500
    assert chaos["impact_pct"] == 50.0
    fake_proc.start.assert_called_once()
    fake_proc.terminate.assert_called_once()
