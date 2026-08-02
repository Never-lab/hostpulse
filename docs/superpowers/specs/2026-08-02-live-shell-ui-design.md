# HostPulse — Live shell UI redesign

**Date:** 2026-08-02  
**Status:** Approved for planning  
**Approach:** Modular CustomTkinter shell (Setup → Live → Done), palette aligned to commercial HTML report, Never-lab presets + custom presets in local config

## Context

Product phases 1–3 (report, cancel/CLI/PDF, platform adapters, light UX polish) shipped. The live GUI (`bin/ui_benchmark.py`) still feels like an internal form: default CTk green dark theme, dense left column, raw log as primary surface. The commercial report is now the polished deliverable; the on-site shell should match that product identity.

**Primary user:** Never-lab technician on-site at the customer (live diagnosis + leave the report).

**Stack constraint:** Keep CustomTkinter + existing `orchestrator.run_audit` / cancel / PDF. No web/.NET rewrite.

## Goals

- Rebuild the live shell as a three-state flow: **Setup → Live → Done**
- Done shows a **mini scorecard** (grade + score/100) before opening HTML
- Visual language shared with the offline HTML report (dark GUI, same brand/accent/status tokens)
- Setup driven by **Never-lab presets** plus **user-saved custom presets** in `config.json`
- Italian UI copy (technician-facing)

## Non-goals

- New UI framework (web, WPF, etc.)
- Light mode in v1
- Changing HTML report layout/content (reuse palette + score only)
- Rewriting CLI
- SaaS / remote agent
- Full custom theming engine beyond token constants

## Architecture

```
bin/ui_benchmark.py          # entry: deps check → AuditApp
bin/ui/
  __init__.py
  theme.py                   # dark tokens aligned to report CSS
  presets.py                 # built-in + load/save UI_PRESETS
  app.py                     # CTk root + state machine
  screens/
    setup.py
    live.py
    done.py
```

**Unchanged contracts:** `orchestrator.run_audit`, cooperative cancel, `pdf_export`, AuditResult JSON schema, engine profiles/flags.

**Minimal orchestrator change:** extend `AuditResultPaths` with fields already known after report generation:

| Field | Source |
|-------|--------|
| `overall_score` | `ReportGenerator.overall["score"]` |
| `grade` | `ReportGenerator.overall["grade"]` |
| `status` | `ReportGenerator.overall["status"]` (`ok`/`warn`/`crit`/`na`) |
| `hostname` | `engine.data["meta"]["hostname"]` |
| `profile` | run profile string |
| `mode` | `production-safe` / `quick` / `full` |

GUI Done screen consumes these; no second scoring path.

**Packaging:** `HostPulse.windows.spec` keeps `pathex=["bin"]`; add `ui`, `ui.theme`, `ui.presets`, `ui.app`, `ui.screens.*` to `hiddenimports` as needed so frozen EXE resolves the package.

## Screen flow

### Setup

- Header: **HostPulse** + `engine_version`
- Preset list: three built-ins + any custom entries
- Primary CTA: **Avvia analisi**
- Collapsed **Avanzate**: profile menu, quick, production-safe, compare. Changing any advanced control marks the selection as **modified** (preset highlight stays as “base”, primary CTA still uses the current flag values). **Salva come preset…** persists those values under a new name.
- **Salva come preset…** → name dialog → append to `UI_PRESETS`, select the new custom preset
- Delete allowed only for custom presets

### Live

- Locked config summary (preset name / profile / mode)
- Step indicator for the six orchestrator phases
- Progress bar + status line (existing `on_progress` callbacks)
- **Annulla** (cooperative cancel)
- Log: collapsible, **expanded by default** for technicians
- On cancel: return to Setup with a clear log/status message; no Done scorecard

### Done

- Large grade (A–D) + score/100 colored by status tokens
- Hostname · profile · mode
- **Apri report** · **Esporta PDF** · **Nuova analisi** (back to Setup)
- Report path in muted text
- PDF failure: messagebox; stay on Done

### Full-load guard

Existing `needs_full_load_confirm` dialog remains **before** entering Live when app/db profile runs without production-safe.

## Presets

### Built-in (not deletable)

| Id / label | profile | quick | production_safe | compare |
|------------|---------|-------|-----------------|---------|
| `DB prod-safe` | `db_server` | false | true | false |
| `App full` | `app_server` | false | false | false |
| `Quick smoke` | `generic` | true | false | false |

### Persistence (`config.json`)

Additive keys only (engine keys unchanged):

```json
{
  "UI_LAST_PRESET": "DB prod-safe",
  "UI_PRESETS": [
    {
      "name": "Mio DB quick",
      "profile": "db_server",
      "quick": true,
      "production_safe": true,
      "compare": false
    }
  ]
}
```

- `config.example.json` documents the keys
- Missing keys → defaults; corrupt custom entries skipped at load (no crash)
- If a custom entry reuses a built-in name, the built-in wins and that custom entry is ignored

## Theme

Dark CustomTkinter; **do not** use `ctk.set_default_color_theme("green")`.

Tokens (aligned to report / chart dark palette):

| Token | Value | Notes |
|-------|-------|-------|
| bg | `#0f172a` | window |
| card | `#1e293b` | panels |
| ink | `#f8fafc` | primary text |
| muted | `#94a3b8` | secondary |
| border | `#334155` | |
| brand | `#0c4a6e` | header accent |
| accent | `#0284c7` | primary buttons / progress |
| ok | `#16a34a` | |
| warn | `#d97706` | |
| crit | `#dc2626` | |

Status colors match `STATUS_COLORS` in `reporter_generator.py`. Prefer a single shared constant module later only if duplication hurts; for this change, `ui/theme.py` may duplicate the hex values with a comment pointing at the report.

Typography: Segoe UI for chrome; Consolas (or ui-monospace) for log — same family as report.

## Error handling

| Case | Behavior |
|------|----------|
| Missing deps at startup | existing `require_dependencies` exit |
| Full load on app/db | confirm dialog; abort stays on Setup |
| Cancel mid-run | Setup + message |
| Audit exception | messagebox + Setup; log last error |
| PDF export fail | messagebox; remain on Done |
| Preset save fail | messagebox; keep prior presets |

## Testing / verification

- Unit: `presets` roundtrip (builtin merge, save custom, reject delete of builtin, last-preset restore)
- Unit/smoke: import `ui` package and construct theme constants
- Optional: state machine transition Setup→Live→Done with mocked `run_audit` returning fake `AuditResultPaths`
- Manual (Windows): GUI starts; Start enabled; run quick smoke preset; Done shows grade; Open report / PDF / Nuova analisi
- Piece-check from CLAUDE.md: GUI starts; start button enabled; EXE build still finds entry if packaging touched

## Success criteria

- Technician can pick a Never-lab preset and start in ≤2 clicks after launch
- During run, phase + cancel are obvious without reading the log
- After run, grade/score visible before opening HTML
- GUI and HTML report feel like the same product (palette + status language)
- Custom preset survives restart via `config.json`

## Open decisions (resolved)

| Topic | Decision |
|-------|----------|
| Scope | Full shell rebuild, modular `bin/ui/` |
| User | Technician on-site |
| Flow | Setup → Live → Done + mini scorecard |
| Look | Dark + report palette |
| Setup density | Presets + custom save; advanced collapsed |
| Architecture | Approach 2 — modular package |
