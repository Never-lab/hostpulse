# Deployment – HostPulse

**Contesto:** HostPulse viene distribuito ai clienti come **pacchetto pronto** (Windows EXE o Linux zip + launcher), non solo come sorgente da sviluppo. L’esecuzione tipica è su **VM in produzione** (application server o DB server); usare il **profilo** e **Esecuzione in produzione (carico ridotto)** per adattare soglie e ridurre l’impatto.

## Download (Releases)

Tag `vX.Y.Z` su GitHub → [Releases](https://github.com/Never-lab/hostpulse/releases/latest):

| Asset | Piattaforma | Contenuto |
|-------|-------------|-----------|
| `HostPulse-windows.zip` | Windows | `HostPulse.exe`, `config/config.json`, `results/` |
| `HostPulse-linux.zip` | Linux | `hostpulse.sh`, `bin/`, `config/`, `requirements.txt`, `results/` |

## Windows (EXE)

1. Scarica ed estrai `HostPulse-windows.zip` sulla VM Windows.
2. **Distribuisci l’intera cartella** `HostPulse\` (`HostPulse.exe`, `_internal\`, `config\`, `results\`).
3. Avvia `HostPulse.exe` (GUI).
4. Se Defender/SmartScreen blocca: vedi [docs/WINDOWS_AV.md](docs/WINDOWS_AV.md) (SHA256, esclusione cartella, firma).

Build locale: `.\build_exe.ps1` → `dist\windows\HostPulse\`.

## Linux (zip + hostpulse.sh)

**Prerequisiti:** Python 3.10+ con modulo `venv` (`python3-venv` su Debian/Ubuntu), display opzionale (solo per GUI).

1. Scarica ed estrai `HostPulse-linux.zip`.
2. Esegui (primo avvio crea `.venv/` e installa `requirements.txt` — compatibile PEP 668):

   ```bash
   cd HostPulse
   ./hostpulse.sh run --quick --production-safe --out results/report.html
   ```

   Su Debian/Ubuntu, se il venv non si crea:

   ```bash
   sudo apt install python3-venv python3-pip
   ```

3. Comandi:

   - `./hostpulse.sh` — GUI se `DISPLAY` è impostato, altrimenti audit headless rapido in production-safe.
   - `./hostpulse.sh gui` — forza GUI.
   - `./hostpulse.sh run …` — pass-through verso `bin/cli.py run` (profili, `--pdf`, ecc.).

4. Metriche non disponibili su Linux → INFO `PLATFORM_*_NA` nel report (non crash). Dettaglio: [docs/PLATFORM.md](docs/PLATFORM.md).

Build locale: `./build_linux.sh` → `dist/linux/HostPulse/` + `dist/HostPulse-linux.zip`.

## Percorsi runtime

L’engine usa la **cartella del pacchetto** come root (`config/`, `results/`). Con l’exe Windows la root è la cartella dell’exe; con Linux la root è dove vive `hostpulse.sh` (vedi `bin/app_paths.py`).

## Dipendenze

- **Windows EXE:** tutte le librerie di `requirements.txt` sono incluse nel bundle PyInstaller.
- **Linux zip:** primo avvio di `hostpulse.sh` crea `.venv/` locale e installa dipendenze; override con `HOSTPULSE_PYTHON`.

## Configurazione (`config/config.json`)

- `PROFILE`: `"generic"` | `"app_server"` | `"db_server"`
- `PRODUCTION_SAFE`: `true` — riduce carico su VM produzione
- `WARN_DB_LATENCY_MS`: soglia latenza disco (ms) profilo DB (es. 10)
- `DISK_TEST_PATH`: directory test disco (es. volume dati); vuoto = temp di sistema
- `APP_PORT_CHECK`: porta/e per profilo app server; `null` = nessun check

Vedi anche [docs/SCHEMA.md](docs/SCHEMA.md).
