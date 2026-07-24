#!/usr/bin/env python3
"""Headless HostPulse CLI (no CustomTkinter import)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_BIN = Path(__file__).resolve().parent
if str(_BIN) not in sys.path:
    sys.path.insert(0, str(_BIN))

from app_paths import ensure_runtime_dirs, get_app_base_dir, get_bin_dir  # noqa: E402
from cancel import AuditCancelled  # noqa: E402
from load_safety import CLI_FULL_LOAD_WARN, needs_full_load_confirm  # noqa: E402
from orchestrator import run_audit  # noqa: E402
from pdf_export import PdfExportError, html_file_to_pdf  # noqa: E402


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="hostpulse", description="HostPulse headless audit")
    sub = p.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run audit and write HTML report")
    run.add_argument("--profile", choices=("generic", "app_server", "db_server"), default="generic")
    run.add_argument("--quick", action="store_true")
    run.add_argument("--production-safe", action="store_true")
    run.add_argument("--compare", action="store_true", help="Compare with previous results")
    run.add_argument("--out", type=Path, default=None, help="HTML output path (default: bin/REPORT_<host>.html)")
    run.add_argument("--pdf", type=Path, nargs="?", const=True, default=None, help="Export PDF (optional path)")
    run.add_argument("--no-slides", action="store_true", help="Skip PNG slide asset export")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command != "run":
        return 2

    ensure_runtime_dirs()
    root = str(get_app_base_dir())
    bin_dir = str(get_bin_dir())

    if needs_full_load_confirm(args.profile, args.production_safe):
        print(CLI_FULL_LOAD_WARN, file=sys.stderr)

    def on_progress(_status: str, _step: int, log: str) -> None:
        print(log, flush=True)

    try:
        result = run_audit(
            root_dir=root,
            bin_dir=bin_dir,
            profile=args.profile,
            quick=args.quick,
            production_safe=args.production_safe,
            compare=args.compare,
            export_slides=not args.no_slides,
            on_progress=on_progress,
        )
    except AuditCancelled as exc:
        print(f"CANCELLED: {exc}", file=sys.stderr)
        return 130
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    html_path = Path(result.html_path)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(html_path.read_text(encoding="utf-8"), encoding="utf-8")
        html_path = args.out.resolve()

    print(html_path)

    if args.pdf is not None:
        pdf_target = None if args.pdf is True else Path(args.pdf)
        try:
            pdf_path = html_file_to_pdf(html_path, pdf_target)
            print(pdf_path)
        except PdfExportError as exc:
            print(f"ERROR PDF: {exc}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
