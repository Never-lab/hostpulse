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
