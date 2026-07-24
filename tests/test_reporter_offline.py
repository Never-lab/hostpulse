from __future__ import annotations

import json
from pathlib import Path

from reporter_generator import ReportGenerator

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "minimal_audit.json"
CDN_MARKERS = (
    "cdn.jsdelivr.net",
    "fonts.googleapis.com",
    "fonts.gstatic.com",
    "chart.js",
)


def test_html_has_no_external_cdn() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    html = ReportGenerator(data, reference=None).render().lower()
    for marker in CDN_MARKERS:
        assert marker not in html, f"CDN/external asset still referenced: {marker}"


def test_html_includes_commercial_sections() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    html = ReportGenerator(data, reference=None).render()
    assert "Come leggere questo report" in html
    assert "Legenda score" in html
    assert "Production-safe" in html or "production" in html.lower()
    assert "<svg" in html.lower()
    assert "HostPulse" in html
