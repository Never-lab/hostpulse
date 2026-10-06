from __future__ import annotations

import copy
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
    # Legitimate Windows zeros must stay numeric (not n/d).
    assert "Queue 0" in html
    assert "Ctx/s 0" in html
    # Executive summary keeps intentional bold markup.
    assert "<b>" in html
    assert "&lt;b&gt;" not in html


def test_render_nd_hover_for_platform_gaps() -> None:
    data = copy.deepcopy(json.loads(FIXTURE.read_text(encoding="utf-8")))
    data["sys_info"]["power_plan"] = "N/A"
    data["virtualization"]["cpu_queue_length"] = 0
    data["ram_hw"]["speed_mhz"] = 0
    data["health"]["events"] = [
        {
            "level": "INFO",
            "code": "PLATFORM_RAM_SPEED_NA",
            "message": 'Velocità RAM "non" <disponibile> su Linux.',
            "timestamp": "2026-10-06 12:00:00",
        },
        {
            "level": "INFO",
            "code": "PLATFORM_CPU_QUEUE_NA",
            "message": "Processor Queue Length non supportato su Linux.",
            "timestamp": "2026-10-06 12:00:00",
        },
        {
            "level": "INFO",
            "code": "PLATFORM_POWER_PLAN_NA",
            "message": "Governor CPU non disponibile.",
            "timestamp": "2026-10-06 12:00:00",
        },
    ]
    html = ReportGenerator(data, reference=None, style="corporate").render()
    assert 'class="nd"' in html
    assert "title=\"Velocità RAM &quot;non&quot; &lt;disponibile&gt; su Linux.\"" in html
    assert "Velocità RAM &quot;non&quot; &lt;disponibile&gt; su Linux." in html
    assert 'title="Processor Queue Length non supportato su Linux."' in html
    assert 'title="Governor CPU non disponibile."' in html
    assert "passa il mouse sopra" in html
    # With CPU queue gap, inventory must not claim Queue 0.
    assert "Queue 0" not in html
