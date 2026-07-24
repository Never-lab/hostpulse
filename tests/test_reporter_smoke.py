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
    # Offline-friendly: phase-1 will remove CDNs; until then just ensure render works.
    assert len(html) > 500
