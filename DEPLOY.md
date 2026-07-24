# Deployment – HostPulse

**Contesto:** questo progetto viene distribuito e eseguito come **eseguibile (.exe) sul cliente** (non solo in ambiente di sviluppo). L’esecuzione tipica è su **VM clienti in produzione** (application server o DB server); usare il **profilo** (Generico / Application Server / DB Server) e l’opzione **Esecuzione in produzione (carico ridotto)** per adattare soglie e ridurre l’impatto.

Da tenere presente in fase di build e packaging (es. PyInstaller, cx_Freeze):

- **Entry point:** avviare l’applicazione dalla GUI, es. `python -m bin.ui_benchmark` oppure script che importa e lancia `ui_benchmark`.
- **Percorsi:** l’engine usa `root_dir` (cartella progetto) per `config/` e `results/`; con l’exe verificare che le risorse (config.json, cartella results) siano raggiungibili dalla posizione in cui gira l’exe (es. stessa cartella dell’exe o percorso fissato in fase di build).
- **Dipendenze:** includere tutte le librerie in `requirements.txt` nel bundle. Se l’applicazione viene avviata come script Python (non exe), all’avvio verifica la presenza delle librerie richieste e, in caso di mancanza, tenta l’installazione automatica con `pip install` (senza usare `requirements.txt`).
- **Windows:** il codice usa PowerShell, WMI e powercfg; l’exe è pensato per ambiente Windows cliente.

**Parametri di configurazione** (in `config/config.json` o `config.example.json`):

- `PROFILE`: `"generic"` | `"app_server"` | `"db_server"` – contesto della macchina (override da UI).
- `PRODUCTION_SAFE`: `true` – riduce carico (durata CPU, MB disco, iterazioni IOPS) per VM in produzione.
- `WARN_DB_LATENCY_MS`: soglia latenza disco (ms) per avviso su profilo DB server (es. 10).
- `DISK_TEST_PATH`: percorso directory per test disco (es. `"D:\\"` per volume dati DB); vuoto = temp di sistema.
- `APP_PORT_CHECK`: porta o lista porte da verificare per profilo app server (es. `8080` o `[8080, 443]`); `null` = nessun check.
