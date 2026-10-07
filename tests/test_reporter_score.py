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
