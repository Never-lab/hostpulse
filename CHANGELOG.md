# Changelog

## 1.4.1 — Report layout fix (Health Score + CPU freq chart)

Renumbered from mistaken tag `v0.4.1` (SemVer 3-part; equivalent to intended `0.1.4.1`).

- Health Score card: full-width layout (no spurious 160px grid column)
- CPU stress chart: frequency polyline uses local SVG coordinates inside the translated panel
- Tests for verdict layout and freq panel coordinates

## 1.4.0 — Linux report polish + safer packaging

Renumbered from `v0.1.4`.

- Report HTML: valori non disponibili come **n/d** con tooltip hover (motivi `PLATFORM_*_NA`)
- Linux: modello CPU da `/proc/cpuinfo`; RAM MHz via `dmidecode` (preferisce configured speed)
- Pacchetto Linux: include `bin/ui/` per la GUI; launcher accetta `HOSTPULSE_PYTHON` assoluto
- Hardening report: escape HTML su inventario/health/summary; filename host sanitizzati
- Windows: PowerShell/WMIC senza `shell=True`

## 1.3.0 — Live shell UI

Renumbered from `v0.1.3`.

- Live GUI: Setup → Live → Done shell, report-aligned dark theme, Never-lab presets (+ custom in config)
- Report HTML: layout commerciale (hero, score ring, KPI con stato, metriche raggruppate)
- Grafico CPU: assi etichettati, griglia 0–100%, media/picco/min, pannello MHz separato
- Windows EXE: onedir (no UPX), version resource, SHA256.txt, firma Authenticode opzionale — [docs/WINDOWS_AV.md](docs/WINDOWS_AV.md)
- Fix Release workflow: avoid secrets in `if:` (restores tag-triggered builds)

## 1.2.0 — Linux venv bootstrap (PEP 668)

Renumbered from `v0.1.2`.

- Linux `hostpulse.sh`: auto-bootstrap local `.venv` on first run (Debian/Ubuntu externally-managed-environment)

## 1.1.0 — Linux client package + dual-asset release

Renumbered from `v0.1.1`.

- Linux client package: `hostpulse.sh` launcher + `build_linux.sh` → `HostPulse-linux.zip`
- Release workflow publishes both Windows EXE and Linux zip on tag `v*`
- `scripts/verify_local.sh` for Linux/WSL; CI smoke on Ubuntu

## 1.0.0 — first public release

Renumbered from `v0.1.0`.

- Commercial offline HTML report + optional PDF (Edge/Chrome headless)
- Versioned `AuditResult` schema (`schema_version` / `engine_version`)
- GUI (CustomTkinter) + headless CLI (`python bin/cli.py run …`)
- Cooperative cancel, production-safe / quick modes, app/db profiles
- Platform adapters: Windows production path, Linux best-effort (`docs/PLATFORM.md`)
- CI, Dependabot, Windows EXE release asset via tag `v*`
