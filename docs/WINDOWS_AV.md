# Windows — antivirus e SmartScreen

HostPulse è distribuito come **EXE PyInstaller non firmato** (salvo release firmate in futuro). Alcuni antivirus (Microsoft Defender, SmartScreen, EDR aziendali) possono segnalarlo come minaccia **anche se il file è legittimo** — è un falso positivo frequente su tool Python impacchettati.

## Cosa facciamo nel build

| Mitigazione | Perché |
|-------------|--------|
| **onedir** invece di onefile | Niente estrazione in `%TEMP%` a ogni avvio (comportamento tipico del malware) |
| **UPX disabilitato** | I packer compressi alzano molto i falsi positivi |
| **Version resource** | `ProductName`, `FileVersion`, `CompanyName` nell’EXE |
| **SHA256.txt** nel pacchetto | Verifica integrità vs [GitHub Releases](https://github.com/Never-lab/hostpulse/releases/latest) |
| **Firma Authenticode** (opzionale) | Se configuri un certificato code signing in CI o in locale |

## Verifica integrità (consigliato al cliente)

Dopo aver estratto `HostPulse-windows.zip`:

```powershell
Get-FileHash -Algorithm SHA256 .\HostPulse.exe
# confronta con SHA256.txt nella stessa cartella o con l’hash pubblicato nella Release
```

## Per l’IT / il cliente (esclusione controllata)

Se Defender blocca l’esecuzione su una VM di audit:

1. Verificare SHA256 come sopra.
2. Esclusione **solo sulla cartella** del tool (non disabilitare Defender globalmente):

   ```powershell
   Add-MpPreference -ExclusionPath "D:\Tools\HostPulse"
   ```

3. Oppure: **Sicurezza di Windows → Protezione da virus e minacce → Gestisci impostazioni → Esclusioni**.

Distribuire sempre l’**intera cartella** `HostPulse\` (`HostPulse.exe` + `_internal\` + `config\`), non copiare solo l’exe.

## Firma code signing (soluzione definitiva)

Per eliminare quasi del tutto SmartScreen/Defender in produzione serve un certificato **Authenticode** (OV o EV) e firmare l’EXE.

### Build locale

```powershell
$env:HOSTPULSE_SIGN_PFX = 'C:\path\codesign.pfx'
$env:HOSTPULSE_SIGN_PASSWORD = '***'
.\build_exe.ps1
```

### GitHub Actions (release)

Aggiungi repository secrets:

- `WINDOWS_SIGN_PFX_BASE64` — contenuto del `.pfx` in base64
- `WINDOWS_SIGN_PASSWORD` — password del certificato

La workflow Release firmerà automaticamente se i secret sono presenti.

## Segnalare falso positivo a Microsoft

Se Defender classifica HostPulse con un nome specifico (es. `Trojan:Win32/...`):

1. [Microsoft Security Intelligence — submission](https://www.microsoft.com/en-us/wdsi/filesubmission)
2. Scegli **Software developer** / false positive, allega `HostPulse.exe` e SHA256.
3. Ripeti dopo ogni major release se necessario.

## Alternative senza EXE

- **Linux**: `HostPulse-linux.zip` + `hostpulse.sh` (nessun PyInstaller).
- **Sorgente**: `pip install -r requirements.txt` + `python bin/ui_benchmark.py` su VM con Python.
