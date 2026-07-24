# HostPulse — hardware/OS benchmark e report

```bash
cd bin
python ui_benchmark.py
```

Dipendenze: `pip install -r requirements.txt`  
(all’avvio da sorgente prova anche l’install automatica dei pacchetti mancanti).

## Config

Copia `config/config.example.json` → `config/config.json` e adatta profilo / soglie.

- `PROFILE`: `generic` | `app_server` | `db_server`
- `PRODUCTION_SAFE`: riduce carico su VM in produzione

Dettagli deploy: [DEPLOY.md](DEPLOY.md).

## Build EXE Windows

Da Windows: `.\build_exe.ps1`  
Da Linux (Docker): `python build_exe_windows.py`

Pacchetto atteso: `dist/windows/HostPulse/` (`HostPulse.exe` + `config/` + `results/`).
