from __future__ import annotations

import json
from pathlib import Path

from engine import HostPulseEngine
from version import __version__


ROOT = Path(__file__).resolve().parents[1]


def test_version_is_semverish() -> None:
    parts = __version__.split(".")
    assert len(parts) >= 2
    assert all(p.isdigit() for p in parts[:2])


def test_config_example_loads() -> None:
    path = ROOT / "config" / "config.example.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data.get("PROFILE") in ("generic", "app_server", "db_server", None) or "PROFILE" in data
    assert "DISK_SEQ_MB" in data


def test_engine_data_structure_shape() -> None:
    engine = HostPulseEngine(quick=True, profile="generic", production_safe=True)
    data = engine.data
    for key in ("meta", "sys_info", "virtualization", "ram_hw", "disk_hw", "health", "benchmark", "app_server"):
        assert key in data
    assert data["meta"]["profile"] == "generic"
    assert isinstance(data["health"]["events"], list)
    assert "disk" in data["benchmark"]
    assert "cpu_consistency" in data["benchmark"]
