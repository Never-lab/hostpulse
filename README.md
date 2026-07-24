# HostPulse — hardware/OS benchmark e report

[![CI](https://github.com/Never-lab/hostpulse/actions/workflows/ci.yml/badge.svg)](https://github.com/Never-lab/hostpulse/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Download latest](https://img.shields.io/github/v/release/Never-lab/hostpulse?label=Download%20latest)](https://github.com/Never-lab/hostpulse/releases/latest)

HostPulse misura una VM/host e produce un **report HTML offline** (opzionale PDF) pensato per il cliente.

## Quickstart

```bash
pip install -r requirements.txt
python bin/ui_benchmark.py
# oppure headless:
python bin/cli.py run --quick --production-safe --out report.html
```

Su Windows puoi anche scaricare l’EXE da [Releases](https://github.com/Never-lab/hostpulse/releases/latest).

## Cosa misura

- **CPU** — coerenza/jitter, hash crypto, compressione
- **RAM** — uso, swap, stima bandwidth di copia (+ velocità MHz su Windows)
- **Disco** — sequenziale, IOPS/latenza (path configurabile `DISK_TEST_PATH`)
- **Rete** — ping latenza/jitter verso target configurabile
- **Chaos** — impatto IOPS sotto carico CPU (saltato in production-safe)

Profili: `generic` · `app_server` · `db_server`. Flag indipendenti: `--quick`, `--production-safe`.

## Report (snippet)

Il report include health score, summary in linguaggio semplice, tabella metriche e raccomandazioni — apribile offline senza CDN.

```text
HostPulse Report · hostname · profile=db_server · production-safe
Health Score  B  ·  VM detected · disk latency OK
…
```

GUI: avvia analisi → log live → **Apri report** / **Esporta PDF**.

## Dipendenze e dev

`pip install -r requirements.txt`  
(se manca un package all’avvio GUI, HostPulse esce con un messaggio chiaro — niente `pip install` automatico).

Dev / CI: `pip install -r requirements.txt -r requirements-dev.txt` poi `pytest -q` e `ruff check bin tests`.

Verifica locale (Windows): `.\scripts\verify_local.ps1`  
Con build EXE: `.\scripts\verify_local.ps1 -BuildExe`

## Config

Copia `config/config.example.json` → `config/config.json` e adatta profilo / soglie.

- `PROFILE`: `generic` | `app_server` | `db_server`
- `PRODUCTION_SAFE`: riduce carico su VM in produzione

Dettagli: [DEPLOY.md](DEPLOY.md) · JSON: [docs/SCHEMA.md](docs/SCHEMA.md) · OS: [docs/PLATFORM.md](docs/PLATFORM.md) · [CHANGELOG](CHANGELOG.md).

## Build EXE Windows

Da Windows: `.\build_exe.ps1`  
Da Linux (Docker): `python build_exe_windows.py`

Pacchetto atteso: `dist/windows/HostPulse/` (`HostPulse.exe` + `config/` + `results/`).

Release GitHub: tag `vX.Y.Z` → Actions carica `HostPulse-windows.zip` su [Releases](https://github.com/Never-lab/hostpulse/releases/latest).

## License

MIT — vedi [LICENSE](LICENSE).
