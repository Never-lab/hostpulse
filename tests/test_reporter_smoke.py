from __future__ import annotations

import json
from pathlib import Path

from reporter_generator import ReportGenerator

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "minimal_audit.json"


def test_render_html_from_fixture() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    html = ReportGenerator(data, reference=None, style="corporate").render()
    assert "<!DOCTYPE html>" in html
    assert "HostPulse" in html
    assert "ci-fixture" in html
    assert "Health Score" in html
    # Offline self-contained HTML (no CDN).
    assert len(html) > 500
    assert "cdn.jsdelivr.net" not in html
