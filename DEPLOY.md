# Deployment – HostPulse

**Contesto:** HostPulse viene distribuito ai clienti come **pacchetto pronto** (Windows EXE o Linux zip + launcher), non solo come sorgente da sviluppo. L’esecuzione tipica è su **VM in produzione** (application server o DB server); usare il **profilo** e **Esecuzione in produzione (carico ridotto)** per adattare soglie e ridurre l’impatto.

## Download (Releases)

Tag `vX.Y.Z` su GitHub → [Releases](https://github.com/Never-lab/hostpulse/releases/latest):

| Asset | Piattaforma | Contenuto |
|-------|-------------|-----------|
| `HostPulse-windows.zip` | Windows | Layout **onedir**: `HostPulse.exe`, `_internal\`, `config/`, `results/`, `SHA256.txt` |
| `HostPulse-linux.zip` | Linux | `hostpulse.sh`, `bin/`, `config/` (incl. `baseline.json`), `requirements.txt`, `results/` |
| `SHA256SUMS.txt` | entrambe | Hash SHA256 degli zip (body Release + asset dedicato) |

**Release gate:** il workflow Release fallisce se il tag `vX.Y.Z` non coincide con `bin/version.py` e `pyproject.toml`, o se `pytest` / smoke Linux non passano.

**Build ufficiale Windows:** runner Windows CI + `.\build_exe.ps1` (Python 3.12). Il path Docker `build_exe_windows.py` è deprecato (solo smoke locale non ufficiale).

## Windows (EXE)

1. Scarica ed estrai `HostPulse-windows.zip` sulla VM Windows.
2. **Distribuisci l’intera cartella** `HostPulse\` (`HostPulse.exe`, `_internal\`, `config\`, `results\`). Non copiare solo l’exe.
3. Avvia `HostPulse.exe` (GUI).
4. Verifica integrità: confronta `Get-FileHash .\HostPulse.exe` con `SHA256.txt` nel pacchetto e/o con `SHA256SUMS.txt` / note della Release.
5. Se Defender/SmartScreen blocca: vedi [docs/WINDOWS_AV.md](docs/WINDOWS_AV.md).

Build locale ufficiale: `.\build_exe.ps1` → `dist\windows\HostPulse\` (onedir).

## Linux (zip + hostpulse.sh)

**Prerequisiti:** Python 3.10+ con modulo `venv` (`python3-venv` su Debian/Ubuntu). Per la GUI: display (`DISPLAY`) e Tk (`python3-tk` su Debian/Ubuntu). CLI headless non richiede Tk.

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

   Per la GUI:

   ```bash
   sudo apt install python3-tk
   ```

3. Comandi:

   - `./hostpulse.sh` — GUI se `DISPLAY` è impostato, altrimenti audit headless rapido in production-safe.
   - `./hostpulse.sh gui` — forza GUI (serve `python3-tk`).
   - `./hostpulse.sh run …` — pass-through verso `bin/cli.py run` (profili, `--pdf`, ecc.).

4. Metriche non disponibili su Linux → INFO `PLATFORM_*_NA` nel report (non crash). Dettaglio: [docs/PLATFORM.md](docs/PLATFORM.md).

Build locale: `./build_linux.sh` → `dist/linux/HostPulse/` + `dist/HostPulse-linux.zip`.

### Linux air-gap / offline

Su VM senza PyPI outbound, **non** affidarti al `pip install` del primo avvio. Opzioni:

1. **Prebuilt `.venv`:** su una macchina con rete, crea il venv e installa `requirements.txt`, poi copia l’intera cartella `HostPulse/` (incluso `.venv/`) sulla VM target. Stessa architettura/OS (es. stesso glibc).
2. **`HOSTPULSE_PYTHON`:** punta a un interprete già provisionato (sistema o venv esterno) con le dipendenze installate:

   ```bash
   HOSTPULSE_PYTHON=/opt/hostpulse-venv/bin/python ./hostpulse.sh run --quick --production-safe --out results/report.html
   ```

3. **Mirror / wheelhouse:** se il bootstrap deve restare in loco:

   ```bash
   pip install --no-index --find-links=/media/wheelhouse -r requirements.txt
   ```

   oppure configura `PIP_INDEX_URL` / `pip.conf` verso un mirror interno.

Se `pip` fallisce senza rete, `hostpulse.sh` stampa un hint air-gap e esce con errore.

## Percorsi runtime

L’engine usa la **cartella del pacchetto** come root (`config/`, `results/`). Con l’exe Windows la root è la cartella dell’exe; con Linux la root è dove vive `hostpulse.sh` (vedi `bin/app_paths.py`).

## Dipendenze

- **Windows EXE:** tutte le librerie di `requirements.txt` sono incluse nel bundle PyInstaller onedir.
- **Linux zip:** primo avvio di `hostpulse.sh` crea `.venv/` locale e installa dipendenze (serve rete o mirror); override con `HOSTPULSE_PYTHON` o venv prebuilt (vedi air-gap sopra).

## Configurazione (`config/config.json`)

First-run copies `config/config.example.json` → `config/config.json`. The example
defaults are customer-safe: `PRODUCTION_SAFE: true`, `RAM_TEST_SIZE_MB` /
`DISK_SEQ_MB` at 512 (aligned with engine defaults). Full-load App/DB runs
(`PRODUCTION_SAFE: false`, larger sizes, chaos) are opt-in via UI preset or
explicit config/CLI flags — not the out-of-box path.

- `PROFILE`: `"generic"` | `"app_server"` | `"db_server"`
- `PRODUCTION_SAFE`: `true` — riduce carico su VM produzione (example default)
- `RAM_TEST_SIZE_MB` / `DISK_SEQ_MB`: example ≤ 512; raise only on lab hosts
- `WARN_DB_LATENCY_MS`: soglia latenza disco (ms) profilo DB (es. 10)
- `DISK_TEST_PATH`: directory test disco (es. volume dati); vuoto = temp di sistema
- `APP_PORT_CHECK`: porta/e per profilo app server; `null` = nessun check

Vedi anche [docs/SCHEMA.md](docs/SCHEMA.md).
