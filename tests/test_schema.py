from __future__ import annotations

import json
from pathlib import Path

from engine import HostPulseEngine
from schema import REQUIRED_TOP_LEVEL, SCHEMA_VERSION, stamp_audit
from version import __version__

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "minimal_audit.json"


def test_schema_version_constant() -> None:
    assert SCHEMA_VERSION == 1


def test_new_engine_data_is_stamped() -> None:
    engine = HostPulseEngine(quick=True, profile="generic", production_safe=True)
    assert engine.data["schema_version"] == SCHEMA_VERSION
    assert engine.data["engine_version"] == __version__
    assert engine.data["meta"]["quick"] is True
    assert engine.data["meta"]["production_safe"] is True
    for key in REQUIRED_TOP_LEVEL:
        assert key in engine.data


def test_save_results_writes_versions(tmp_path, monkeypatch) -> None:
    engine = HostPulseEngine(quick=True, production_safe=True)
    monkeypatch.setattr(engine, "results_dir", str(tmp_path))
    path = engine.save_results()
    saved = json.loads(Path(path).read_text(encoding="utf-8"))
    assert saved["schema_version"] == SCHEMA_VERSION
    assert saved["engine_version"] == __version__


def test_fixture_has_schema_fields() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert data["schema_version"] == SCHEMA_VERSION
    assert "engine_version" in data
    for key in REQUIRED_TOP_LEVEL:
        assert key in data


def test_stamp_audit_idempotent() -> None:
    data = {"meta": {}}
    stamp_audit(data, quick=False, production_safe=False)
    stamp_audit(data, quick=True, production_safe=True)
    assert data["schema_version"] == SCHEMA_VERSION
    assert data["meta"]["quick"] is True
    assert data["meta"]["production_safe"] is True
