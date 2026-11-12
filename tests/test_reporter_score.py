from __future__ import annotations

import json
from pathlib import Path

from reporter_generator import ReportGenerator

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "minimal_audit.json"


def _load():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_overall_score_present_and_graded() -> None:
    report = ReportGenerator(_load(), reference=None, style="corporate")
    assert report.overall["score"] > 0
    assert report.overall["grade"] in ("A", "B", "C", "D")
    assert report.overall["status"] in ("ok", "warn", "crit", "na")


def test_zero_throughput_does_not_score_a100() -> None:
    data = _load()
    data["benchmark"]["disk"] = {
        "seq_write_mb": 0,
        "seq_read_mb": 0,
        "iops": 0,
        "latency_p99_ms": 0,
        "db_sim_latency_ms": 0,
    }
    data["benchmark"]["cpu_real"] = {"crypto_hash_rate": 0, "compress_mb_s": 0}
    data["benchmark"]["cpu_consistency"] = {
        "jitter_score": 0,
        "avg_task_ms": 0,
        "stability_score": 0,
    }
    data["benchmark"]["ram_perf"] = {"copy_speed_gb": 0}
    data["benchmark"]["net"] = {"avg_ms": 0, "jitter_ms": 0}
    data["benchmark"]["chaos"] = {
        "active": False,
        "disk_iops_under_load": 0,
        "impact_pct": 0,
    }
    # Healthy usage alone must not produce a commercial A/100.
    data["ram_hw"]["percent_used"] = 40
    data["disk_hw"]["percent_used"] = 40

    report = ReportGenerator(data, reference=None, style="corporate")
    assert not (report.overall["grade"] == "A" and report.overall["score"] >= 100)
    zero_rows = [
        a
        for a in report.analyses
        if a["key"] in ("disk_write", "disk_read", "disk_iops", "crypto", "compress", "ram_bw", "cpu_jitter")
    ]
    assert zero_rows
    assert all(a["status"] == "crit" for a in zero_rows)


def test_latency_zero_remains_scorable() -> None:
    report = ReportGenerator(_load(), reference=None, style="corporate")
    status, _ = report._classify(0.0, good=5, warn=15, higher_is_better=False)
    assert status == "ok"
    status_na, _ = report._classify(None, good=5, warn=15, higher_is_better=False)
    assert status_na == "na"


def test_latency_rows_omitted_when_disk_not_measured() -> None:
    data = _load()
    data["benchmark"]["disk"] = {
        "seq_write_mb": 0,
        "seq_read_mb": 0,
        "iops": 0,
        "latency_p99_ms": 0,
        "db_sim_latency_ms": 0,
    }
    report = ReportGenerator(data, reference=None, style="corporate")
    keys = {a["key"] for a in report.analyses}
    assert "db_latency" not in keys
    assert "db_p99" not in keys


def test_sub_ms_latency_scored_when_disk_ran() -> None:
    data = _load()
    data["benchmark"]["disk"]["seq_write_mb"] = 300
    data["benchmark"]["disk"]["iops"] = 5000
    data["benchmark"]["disk"]["db_sim_latency_ms"] = 0.0
    data["benchmark"]["disk"]["latency_p99_ms"] = 0.0
    report = ReportGenerator(data, reference=None, style="corporate")
    lat = next(a for a in report.analyses if a["key"] == "db_latency")
    assert lat["status"] == "ok"


def test_analyses_include_core_disk_metrics() -> None:
    report = ReportGenerator(_load(), reference=None, style="corporate")
    keys = {a["key"] for a in report.analyses}
    assert "disk_write" in keys
    assert "disk_read" in keys
    assert "disk_iops" in keys


def test_db_profile_tightens_latency_thresholds() -> None:
    base = _load()
    generic = ReportGenerator({**base, "meta": {**base["meta"], "profile": "generic"}}, reference=None)
    db = ReportGenerator({**base, "meta": {**base["meta"], "profile": "db_server"}}, reference=None)
    g_row = next(a for a in generic.analyses if a["key"] == "db_latency")
    d_row = next(a for a in db.analyses if a["key"] == "db_latency")
    assert d_row["good"] < g_row["good"]
    assert d_row["warn"] < g_row["warn"]


def test_html_contains_executive_and_recommendations() -> None:
    html = ReportGenerator(_load(), reference=None).render()
    assert "Executive Summary" in html
    assert "Raccomandazioni" in html
    assert "ci-fixture" in html


def test_html_cpu_chart_has_labeled_axes() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    html = ReportGenerator(data, reference=None).render()
    assert "Utilizzo CPU durante stress test" in html
    assert "Media" in html and "Picco" in html
    assert '0%</text>' in html or "0%" in html


def test_verdict_card_is_full_width() -> None:
    html = ReportGenerator(_load(), reference=None).render()
    assert "grid-template-columns:160px" not in html
    assert ".verdict-row { margin:-20px 0 20px; }" in html


def test_cpu_freq_panel_points_use_local_coords() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    data["benchmark"]["cpu_series"] = {
        "time": [0, 1, 2, 3, 4],
        "usage": [10, 40, 70, 50, 20],
        "freq": [800, 1200, 2200, 1800, 900],
    }
    html = ReportGenerator(data, reference=None).render()
    assert "Frequenza CPU" in html
    assert 'transform="translate(0,308)"' in html
    # Polyline Y must stay inside the local freq panel (rect y=22..110), not absolute SVG space.
    import re

    m = re.search(
        r'<g transform="translate\(0,308\)">.*?<polyline[^>]*points="([^"]+)"',
        html,
        re.S,
    )
    assert m, "freq polyline missing inside translated group"
    ys = [float(p.split(",")[1]) for p in m.group(1).split()]
    assert ys and min(ys) >= 22 and max(ys) <= 110
