# CLAUDE.md — HostPulse

Guidance for agents working in this repository.

> Regole generali (Forge Loop, FABLE+POWERS, note di apprendimento, gate
> umani, lingua, **niente `Co-authored-by: Cursor`**) stanno nel CLAUDE.md
> parent (`~/.claude/CLAUDE.md`). Qui solo ciò che è specifico di HostPulse.

## Project Overview

HostPulse is a **Windows-first** hardware/OS benchmark tool for customer VMs
(app servers / DB servers). Flow:

1. **GUI** (`bin/ui_benchmark.py`, CustomTkinter) starts an audit worker thread
2. **Engine** (`bin/engine.py`, `HostPulseEngine`) collects sysinfo + CPU/RAM/disk/net/chaos
3. Results → JSON under `results/`
4. **Reporter** (`bin/reporter_generator.py`) builds HTML report + PNG slide assets

Distributed as a **PyInstaller EXE** on client machines (see `DEPLOY.md`).

## FABLE + POWERS (HostPulse)

Ordine parent: **Memory → MCP → subagent → loop**. Setup: `/fable`.

### Memory

- Parent: lingua IT in chat, EN in commit/PR salvo diversa indicazione.
- Qui: stack Python, profili, packaging EXE, DoD.
- `claude-mem` a inizio lavoro non triviale prima di riesplorare.
- Agent locale: `doc/AGENT.md` (hub, escluso da git).

### MCP

| Need | Tool |
|------|------|
| Session memory | `claude-mem` (`search` → `timeline` → `get_observations`) |
| GitHub | `gh` on `Never-lab/hostpulse` |
| Code structure | `graphify` on `graphify-out/` |
| GUI smoke (rare) | run GUI locally; Playwright only if it helps |

### Subagent

Fan-out only on real splits (engine vs reporter vs packaging). Merge yourself.
No subagent for one-line tweaks.

### Loop (piece checks)

| Touched | Minimum check before «done» |
|---------|-----------------------------|
| `bin/engine.py` | quick-mode run or targeted method smoke; no crash |
| `bin/reporter_generator.py` | generate HTML from a saved `results/*.json` |
| `bin/ui_benchmark.py` | GUI starts; start button enabled |
| Packaging (`*.spec`, `build_exe*`) | build script completes; `dist/.../HostPulse.exe` exists |
| Any code | `graphify update .` if graphify is available |

Fail → show output → fix → re-run. You declare «done» only after human gate on checklist items.

### POWERS

| | Here means |
|---|------------|
| **P** Design | CustomTkinter dark UI — evolve existing layout, don’t reinvent |
| **O** Plan | `/make-plan` → `/do` or Superpowers for multi-step work |
| **W** Security | Client EXE on prod VMs: no secrets in repo; careful with `pip install` auto-path and PowerShell/`shell=True` |
| **E** Restraint | Karpathy + ponytail **full**: surgical diffs |
| **R** Browser | Open generated HTML report; GUI is desktop not web |

## Commands

```bash
# Dev run (from repo root)
pip install -r requirements.txt
cd bin
python ui_benchmark.py

# Windows EXE
.\build_exe.ps1

# Linux/macOS → Windows EXE via Docker
python build_exe_windows.py
```

Config: copy `config/config.example.json` → `config/config.json` (gitignored).

## Architecture

| Path | Role |
|------|------|
| `bin/app_paths.py` | Dev vs frozen paths (`config/`, `results/`, bundle) |
| `bin/engine.py` | `HostPulseEngine` — collect + benchmark + health events |
| `bin/reporter_generator.py` | Scorecard, HTML, matplotlib/seaborn assets |
| `bin/ui_benchmark.py` | Entry + GUI + worker orchestration |
| `config/baseline.json` | Reference metrics for report deltas |
| `HostPulse.windows.spec` | PyInstaller one-file EXE |

### Profiles

- `generic` | `app_server` | `db_server` (UI + `PROFILE` in config)
- `PRODUCTION_SAFE` / UI checkbox: shorter tests, skip chaos
- `quick`: even shorter durations/iterations

### Data flow

`AuditApp` → `HostPulseEngine` methods → `save_results()` JSON →
`ReportGenerator` → `REPORT_<hostname>.html` + `bin/exports/slides/*.png`

## DoD (definition of done)

- No `Co-authored-by: Cursor` (or other agent co-author trailers) in commits
- Commit author = you (`JustKaneki` / configured identity), never Copilot bot
- Touched path’s piece-check above is green with real command output
- UI/report changes: human ok on checklist before «shipped»
- Local notes only under `docs/apprendimenti/` (gitignored)

## graphify

```bash
graphify update .
graphify query "disk IOPS benchmark"
graphify path "HostPulseEngine" "ReportGenerator"
```

## Learning notes (local only)

`docs/apprendimenti/YYYY-MM-DD-<tema>.md` — Italian, know-how not changelog.
Must stay gitignored (see `.gitignore`).
