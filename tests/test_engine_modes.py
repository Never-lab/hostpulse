from __future__ import annotations

from engine import HostPulseEngine


def test_invalid_profile_falls_back_to_generic() -> None:
    engine = HostPulseEngine(quick=True, profile="nope", production_safe=True)
    assert engine.profile == "generic"
    assert engine.data["meta"]["profile"] == "generic"


def test_quick_mode_caps_config() -> None:
    engine = HostPulseEngine(quick=True, profile="generic", production_safe=False)
    assert engine.config["CPU_GRAPH_DURATION_SEC"] <= 15
    assert engine.config["RAM_TEST_SIZE_MB"] <= 256
    assert engine.config["DISK_SEQ_MB"] <= 128
    assert engine.config["DISK_IOPS_ITERATIONS"] <= 2000


def test_production_safe_caps_and_skips_chaos() -> None:
    engine = HostPulseEngine(quick=False, profile="db_server", production_safe=True)
    assert engine.skip_chaos is True
    assert engine.profile == "db_server"
    assert engine.config["CPU_GRAPH_DURATION_SEC"] <= 30
    assert engine.config["DISK_IOPS_ITERATIONS"] <= 3000


def test_push_health_appends_event() -> None:
    engine = HostPulseEngine(quick=True, production_safe=True)
    engine._push_health("WARN", "TEST_CODE", "hello")
    assert len(engine.data["health"]["events"]) == 1
    ev = engine.data["health"]["events"][0]
    assert ev["level"] == "WARN"
    assert ev["code"] == "TEST_CODE"
    assert ev["message"] == "hello"
    assert "timestamp" in ev
