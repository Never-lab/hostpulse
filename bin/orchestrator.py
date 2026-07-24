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

ProgressFn = Callable[[str, int, str], None]  # status, step 0-4, log line


@dataclass
class AuditResultPaths:
    json_path: str
    html_path: str
    export_dir: str
    cancelled: bool = False


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

    progress(
        "Preparazione motore analisi...",
        0,
        f"Target: {engine.data['meta']['hostname']} | Admin: {engine.data['meta']['is_admin']}",
    )

    progress("Analisi sistema & CPU...", 1, "[1/4] Raccolta informazioni di sistema...")
    engine.collect_sys_info()
    check_cancel(cancel_event)

    if profile == "app_server" and engine.config.get("APP_PORT_CHECK") is not None:
        progress("Analisi sistema & CPU...", 1, "[1/4] Verifica porta applicativa...")
        engine.check_app_port()
        check_cancel(cancel_event)

    progress("Analisi sistema & CPU...", 1, "[1/4] CPU benchmark in corso...")
    engine.cpu_benchmark_suite()
    check_cancel(cancel_event)

    progress("Analisi sistema & CPU...", 1, "[1/4] CPU real-world test...")
    engine.cpu_real_world()
    check_cancel(cancel_event)

    progress("Analisi sistema & CPU...", 1, "[1/4] RAM bandwidth test...")
    engine.ram_benchmark()
    check_cancel(cancel_event)

    progress("Analisi sistema & CPU...", 1, "[1/4] Network latency test...")
    engine.net_benchmark()
    check_cancel(cancel_event)

    progress("Benchmark storage (Seq & IOPS)...", 2, "[2/4] Benchmark disco in corso...")
    engine.disk_benchmarks()
    check_cancel(cancel_event)

    if not production_safe and not engine.skip_chaos:
        progress("Benchmark storage (Seq & IOPS)...", 2, "[2/4] Chaos test (IOPS sotto carico CPU)...")
        engine.chaos_disk_under_load()
        chaos = engine.data["benchmark"]["chaos"]
        if chaos.get("active"):
            progress(
                "Benchmark storage (Seq & IOPS)...",
                2,
                f"[2/4] Chaos: impatto IOPS {chaos.get('impact_pct', 0)}%.",
            )
        check_cancel(cancel_event)

    progress("Salvataggio risultati...", 3, "[3/4] Salvataggio risultati su disco...")
    json_path = engine.save_results()
    check_cancel(cancel_event)

    progress("Generazione report...", 4, "[4/4] Generazione report...")
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

    progress("Completato", 4, f"Report HTML: {html_path}")
    return AuditResultPaths(json_path=json_path, html_path=html_path, export_dir=export_dir)
