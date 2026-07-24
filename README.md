# HostPulse — hardware/OS benchmark e report

[![CI](https://github.com/Never-lab/hostpulse/actions/workflows/ci.yml/badge.svg)](https://github.com/Never-lab/hostpulse/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Download latest](https://img.shields.io/github/v/release/Never-lab/hostpulse?label=Download%20latest)](https://github.com/Never-lab/hostpulse/releases/latest)

```bash
cd bin
python ui_benchmark.py
```

Dipendenze: `pip install -r requirements.txt`  
(all’avvio da sorgente prova anche l’install automatica dei pacchetti mancanti).

Dev / CI: `pip install -r requirements.txt -r requirements-dev.txt` poi `pytest -q` e `ruff check bin tests`.

Verifica locale (Windows): `.\scripts\verify_local.ps1`  
Con build EXE: `.\scripts\verify_local.ps1 -BuildExe`

## Config

Copia `config/config.example.json` → `config/config.json` e adatta profilo / soglie.

- `PROFILE`: `generic` | `app_server` | `db_server`
- `PRODUCTION_SAFE`: riduce carico su VM in produzione

Dettagli deploy: [DEPLOY.md](DEPLOY.md).

## Build EXE Windows

Da Windows: `.\build_exe.ps1`  
Da Linux (Docker): `python build_exe_windows.py`

Pacchetto atteso: `dist/windows/HostPulse/` (`HostPulse.exe` + `config/` + `results/`).

Release GitHub: tag `vX.Y.Z` → Actions carica `HostPulse-windows.zip` su [Releases](https://github.com/Never-lab/hostpulse/releases/latest).

## License

MIT — vedi [LICENSE](LICENSE).
