# Phase 1b (#2 #9 #14) Implementation Plan

> Batch PR: cancel + CLI + PDF. Branch `feat/phase-1b-cancel-cli-pdf`

**Goal:** Cooperative cancel, headless CLI without GUI deps, HTML→PDF export.

**Architecture:** Shared `run_audit()` orchestrator used by GUI and CLI; `cancel_event` checked between phases and in long engine loops; PDF via headless Edge/Chrome print-to-PDF (no heavy PDF lib).

**Tech:** threading.Event, argparse CLI, subprocess browser print.

## Tasks
1. `bin/cancel.py` + engine `_check_cancel` in long loops
2. `bin/orchestrator.py` `run_audit(...)` → paths dict
3. Wire GUI cancel + use orchestrator
4. `bin/cli.py` headless (no customtkinter import)
5. `bin/pdf_export.py` + GUI button + CLI `--pdf`
6. Tests + verify_local; PR
