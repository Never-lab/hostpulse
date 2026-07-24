# HostPulse — Product direction design

**Date:** 2026-07-24  
**Status:** Draft for user review  
**Approach:** Report-first, keep Python (hybrid UI deferred); Windows production now, Linux-ready architecture

## Context

HostPulse is a hardware/OS benchmark tool aimed at customer VMs (app / DB servers). Today it ships as a Windows PyInstaller EXE: CustomTkinter GUI → `HostPulseEngine` → JSON under `results/` → HTML report (+ PNG slide assets).

**Product goal (confirmed):** live diagnosis **and** a commercial deliverable report, with the **report as the commercial priority**.

**Stack posture (confirmed):** evolve Python; hybrid shell later only if needed; **do not lock to Windows** — Linux executability is a future requirement, so core design must stay portable.

**Primary pain (confirmed):** everything is a bit rough; the **first win must be the commercial report**.

## Decision summary

| Choice | Decision |
|--------|----------|
| Strategy | Approach 1 — report-first on Python |
| Hybrid .NET/WPF/WebView2 | **Out** as primary path (Windows lock + Linux conflict) |
| Languages | Keep Python for engine, reporter, shell |
| First deliverable | Client-ready HTML report (+ PDF path); versioned `AuditResult` schema |
| Platforms | Windows = production path now; Linux = adapters + best-effort in a later phase |

## Architecture

```
┌─────────────────────────────┐
│  Shell (GUI / CLI)          │  now: CustomTkinter; later: same contract
├─────────────────────────────┤
│  Orchestrator               │  profile, quick/prod-safe, progress, cancel
├─────────────────────────────┤
│  Engine                     │  produces AuditResult (versioned JSON)
├──────────┬──────────────────┤
│ Platform │  win / linux     │  OS-specific probes only
└──────────┴──────────────────┘
         ↓
┌─────────────────────────────┐
│  Reporter                   │  HTML (+ PDF) — OS-UI independent
└─────────────────────────────┘
```

**Anti-Windows-lock rules:**

- No WPF / WinUI / WebView2 as the only UI path
- Windows-only APIs (PowerShell, `ping -n`, admin ctypes, WMI) live only behind `platform/` adapters
- Report output and JSON schema are identical on Windows and Linux
- Packaging is per-OS (PyInstaller or equivalent); core must not hardcode `C:\` or EXE-only assumptions

## Report (phase 1 priority)

### Required content (every run)

- Header: hostname, date, profile (`generic` / `app_server` / `db_server`), flags (quick and/or production-safe — independent booleans)
- Health Score + grade (A–D) with a short legend
- Executive summary in plain language (3–5 bullets)
- Metrics table: value · verdict · vs baseline (when present)
- Health events + actionable recommendations
- Short “How to read this report” blurb

### Formats

- **HTML self-contained (must):** opens offline on locked-down Server; no required CDN (Chart.js / Google Fonts). Embed assets or use static SVG / inline CSS.
- **PDF:** same content, one-click from GUI/CLI. If PDF libs blow up the Windows build, phase **1b** may ship “open HTML → print to PDF” first, then a native export path.

### Reporter cleanup

- Remove hard dependency on external CDN/fonts in shipped HTML
- PNG slide exports remain a secondary/internal path, not the customer deliverable
- Profile-specific thresholds and copy (DB vs App) must be explicit in the report text
- Prefer thinning `seaborn` / `pandas` if they are not essential to the customer HTML

### Data contract

Reporter and GUI consume only a versioned **`AuditResult`** JSON (`schema_version`, `engine_version`). On-disk `results/*.json` stay the interchange format on every OS.

## Engine, schema, platforms

### AuditResult (stable surface)

Keep/clarify: `meta`, `sys_info`, `virtualization`, `ram_hw`, `disk_hw`, `health.events[]`, `benchmark.*`, `app_server`, plus `schema_version` and `engine_version`.

### Platform adapters

| Capability | Windows (today) | Linux (future) |
|------------|-----------------|----------------|
| Elevated privileges | `IsUserAnAdmin` | `os.geteuid() == 0` |
| Power / perf plan | `powercfg` | governor / `cpupower` or N/A + INFO |
| RAM speed / HW extras | WMI/CIM | `/sys` or N/A |
| Queue / ctx switches | Perf counters | `/proc` best-effort |
| VM detect | WMI manufacturer | DMI / `systemd-detect-virt` |
| Ping | `ping -n` | `ping -c` |
| Disk test path | path / drive | mount path |

Missing capability → metric `null` + health `INFO`/`WARN` (“unsupported on this platform”), never crash.

### Orchestrator

Owns test sequence, progress callbacks, **cooperative cancel** (missing today), and flags: quick / production-safe / profile. GUI and future CLI call the same orchestrator.

### Engine dependencies

Prefer `psutil` + stdlib. PowerShell only inside the Windows adapter. No new language for the core.

## Shell, packaging, roadmap

### Shell

- **Now:** CustomTkinter for live diagnosis (progress, log, open report, PDF when available)
- **Cancel:** cooperative flag between steps / inside long loops (not hard kill)
- **CLI (same orchestrator):** introduce a proper package layout when needed (today code lives under `bin/`); target UX e.g. `python -m hostpulse run --profile db_server --production-safe --out report.html` for headless Server and future Linux
- Future “modern UI” must stay cross-platform (Python shell evolution), not .NET

### Packaging

- Windows: current PyInstaller layout (`HostPulse.exe` + `config/` + `results/`)
- Linux (future): same layout (binary or entrypoint + config/results)
- Mental build matrix: `windows` | `linux`

### Phased roadmap

| Phase | Focus | Done when |
|-------|--------|-----------|
| **1** | Commercial report + `schema_version` + offline HTML | Report is client-sendable; JSON contract stable |
| **1b** | PDF + cooperative cancel + minimal CLI | One-click PDF path; Cancel / Ctrl+C useful |
| **2** | Platform adapters + Linux best-effort | Runs on Linux without crash; gaps documented |
| **3** | Live UX polish / optional new Python shell | Only after report is already “the product” |

### Non-goals

- C# / WPF rewrite
- SaaS, remote agent, centralized fleet
- Full Linux feature parity in phase 1
- Relying on auto-`pip install` inside frozen EXE (dev may keep or replace with a clear missing-deps message)

## Testing / verification (design-level)

- Phase 1: generate HTML from a fixture `results/*.json`; open offline (no network); spot-check summary/score/metrics
- Phase 1b: PDF opens; cancel stops before next major step
- Phase 2: Linux smoke run completes or fails soft with documented N/A metrics

## Open points resolved in this design

- PDF timing: required path exists; native lib vs print-to-PDF may land in 1b if build cost is high
- Hybrid UI: deferred and constrained to cross-platform options only
- Linux: architectural readiness in phase 1; implementation in phase 2

## Out of scope for the first implementation plan

Full Linux adapters, new GUI framework, C# anything, SaaS. The first plan should target **phase 1** (and optionally the cheap parts of **1b** if they fit cleanly).
