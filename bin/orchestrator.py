"""Shared audit runner for GUI and CLI."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Any, Callable, Optional

from cancel import check_cancel
from engine import HostPulseEngine
from reporter_generator import ReportGenerator

# step index for progress bar: 0..PROGRESS_TOTAL
PROGRESS_TOTAL = 6

ProgressFn = Callable[[str, int, str], None]  # status, step, log line


@dataclass
class AuditResultPaths:
    json_path: str
    html_path: str
    export_dir: str
    cancelled: bool = False
    overall_score: float = 0.0
    grade: str = "N/A"
    status: str = "na"
    hostname: str = ""
    profile: str = "generic"
    mode: str = "full"


def _load_baseline(root: str) -> Any:
    path = os.path.join(root, "config", "baseline.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as bf:
            return json.load(bf)
    except (json.JSONDecodeError, OSError):
        return None


def run_audit(
    *,
    root_dir: str,
    bin_dir: str,
    profile: str = "generic",
    quick: bool = False,
    production_safe: bool = False,
    compare: bool = False,
    export_slides: bool = True,
    cancel_event: Optional[Event] = None,
    on_progress: Optional[ProgressFn] = None,
) -> AuditResultPaths:
    """Run full audit pipeline. Raises AuditCancelled if cancel_event is set."""

    def progress(status: str, step: int, log: str) -> None:
        check_cancel(cancel_event)
        if on_progress:
            on_progress(status, step, log)

    engine = HostPulseEngine(
        root_dir=root_dir,
        quick=quick,
        profile=profile,
        production_safe=production_safe,
    )
    engine.cancel_event = cancel_event

    mode = "production-safe" if production_safe else ("quick" if quick else "full")
    progress(
        "0/6 · Preparazione",
        0,
        f"Host {engine.data['meta']['hostname']} · profilo={profile} · modo={mode} · admin={engine.data['meta']['is_admin']}",
    )

    progress("1/6 · Sistema", 1, "[1/6] Raccolta informazioni di sistema...")
    engine.collect_sys_info()
    check_cancel(cancel_event)

    if profile == "app_server" and engine.config.get("APP_PORT_CHECK") is not None:
        progress("1/6 · Sistema", 1, "[1/6] Verifica porta applicativa...")
        engine.check_app_port()
        check_cancel(cancel_event)

    progress("2/6 · CPU", 2, "[2/6] CPU consistency...")
    engine.cpu_benchmark_suite()
    check_cancel(cancel_event)
    progress("2/6 · CPU", 2, "[2/6] CPU real-world (hash/compress)...")
    engine.cpu_real_world()
    check_cancel(cancel_event)

    progress("3/6 · RAM e rete", 3, "[3/6] Bandwidth RAM...")
    engine.ram_benchmark()
    check_cancel(cancel_event)
    progress("3/6 · RAM e rete", 3, "[3/6] Ping / latenza rete...")
    engine.net_benchmark()
    check_cancel(cancel_event)

    progress("4/6 · Disco", 4, "[4/6] Benchmark disco (seq + IOPS)...")
    engine.disk_benchmarks()
    check_cancel(cancel_event)

    if not production_safe and not engine.skip_chaos:
        progress("4/6 · Disco", 4, "[4/6] Chaos: IOPS sotto carico CPU...")
        engine.chaos_disk_under_load()
        chaos = engine.data["benchmark"]["chaos"]
        if chaos.get("active"):
            progress(
                "4/6 · Disco",
                4,
                f"[4/6] Chaos: impatto IOPS {chaos.get('impact_pct', 0)}%.",
            )
        check_cancel(cancel_event)
    elif production_safe:
        progress("4/6 · Disco", 4, "[4/6] Chaos saltato (production-safe).")

    progress("5/6 · Salvataggio", 5, "[5/6] Scrittura JSON risultati...")
    json_path = engine.save_results()
    check_cancel(cancel_event)

    progress("6/6 · Report", 6, "[6/6] Generazione report HTML...")
    ref = _load_baseline(root_dir)
    if compare:
        reporter = ReportGenerator(engine.get_history(), reference=ref, style="corporate")
    else:
        reporter = ReportGenerator(engine.data, reference=ref, style="corporate")

    export_dir = os.path.join(bin_dir, "exports", "slides")
    if export_slides:
        os.makedirs(export_dir, exist_ok=True)
        reporter.export_presentation_assets(export_dir)

    report_html = f"REPORT_{engine.data['meta']['hostname']}.html"
    html_path = os.path.join(bin_dir, report_html)
    Path(html_path).write_text(reporter.render(), encoding="utf-8")

    progress("Completato", PROGRESS_TOTAL, f"Report pronto: {html_path}")
    overall = getattr(reporter, "overall", {}) or {}
    return AuditResultPaths(
        json_path=json_path,
        html_path=html_path,
        export_dir=export_dir,
        overall_score=float(overall.get("score", 0) or 0),
        grade=str(overall.get("grade", "N/A")),
        status=str(overall.get("status", "na")),
        hostname=str(engine.data.get("meta", {}).get("hostname", "")),
        profile=profile,
        mode=mode,
    )
