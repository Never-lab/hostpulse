from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from disk_io import measure_random_read_latencies
from engine import HostPulseEngine
from reporter_generator import ReportGenerator

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "minimal_audit.json"


def test_disk_benchmarks_sets_iops_mode(tmp_path) -> None:
    engine = HostPulseEngine(quick=True, production_safe=False)
    engine.config["DISK_SEQ_MB"] = 1
    engine.config["DISK_IOPS_ITERATIONS"] = 40
    engine.config["DISK_TEST_PATH"] = str(tmp_path)
    engine.disk_benchmarks()
    mode = engine.data["benchmark"]["disk"]["iops_mode"]
    assert mode in ("unbuffered", "cached")
    assert engine.data["benchmark"]["disk"]["iops"] >= 0


def test_measure_random_read_falls_back_to_cached(tmp_path) -> None:
    path = tmp_path / "t.bin"
    path.write_bytes(b"x" * (64 * 1024))
    with patch("disk_io.platform.system", return_value="Darwin"):
        latencies, mode = measure_random_read_latencies(str(path), 64 * 1024, 20)
    assert mode == "cached"
    assert len(latencies) > 0


def test_reporter_shows_dual_net_and_iops_mode() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    report = ReportGenerator(data, reference=None, style="corporate")
    keys = {a["key"] for a in report.analyses}
    assert "net_latency_internet" in keys
    assert "net_latency_gateway" in keys
    iops = next(a for a in report.analyses if a["key"] == "disk_iops")
    assert "unbuffered" in iops["label"]
    ram = next(a for a in report.analyses if a["key"] == "ram_bw")
    assert ram["good"] == 1.5
    assert ram["warn"] == 0.8
    html = report.render()
    assert "Gateway" in html
    assert "page cache" in html or "unbuffered" in html
    assert "utente→server" in html or "utente&#8594;server" in html or "utente" in html


def test_cached_high_iops_marked_info() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    data["benchmark"]["disk"]["iops"] = 600000
    data["benchmark"]["disk"]["iops_mode"] = "cached"
    report = ReportGenerator(data, reference=None, style="corporate")
    iops = next(a for a in report.analyses if a["key"] == "disk_iops")
    assert iops["status"] == "info"
    assert "cache" in iops["verdict"].lower()
