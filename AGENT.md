# AGENT.md — HostPulse (hub operativo)

Fonte di verità per agent e maintainer. Brief prodotto: [`CLAUDE.md`](./CLAUDE.md).  
Cursor carica anche [`AGENTS.md`](./AGENTS.md) (stub → questo file).

---

## Regola d’oro — ogni release

**Prima di bumpare versione / taggare / pubblicare assets: esegui l’audit release sotto.**  
Non saltarlo perché “è solo un fix piccolo”. L’output dell’audit sono issue GitHub (o conferma “nessuna nuova issue”).

Ordine obbligato:

1. **Audit release** (checklist sotto) → apri/aggiorna issue
2. Implementa solo ciò che deve entrare *in questa* release
3. Piece-check (`CLAUDE.md` loop) + `pytest -q`
4. Bump `bin/version.py` + `pyproject.toml` + `CHANGELOG.md` (stesso `X.Y.Z`)
5. Tag `vX.Y.Z` su commit allineato → workflow Release
6. Smoke pacchetti (`HostPulse-windows.zip` intera cartella con `_internal\`; Linux `./hostpulse.sh run --quick --production-safe`)

---

## Audit release (checklist)

Copia in chat / issue epic e spunta. Ogni finding non banale → `gh issue create` con label `priority:*` + area.

### A. Versione & release hygiene

- [ ] `bin/version.py` == `pyproject.toml` == prossimo tag `vX.Y.Z` (SemVer **3** parti; niente `0.1.4.1`)
- [ ] `CHANGELOG.md` ha sezione per la release
- [ ] Nessun tag “zompato” (`0.4.1`-style); linea attuale **1.x** (storici `0.1.N` → `1.N.0`)
- [ ] Workflow Release: dopo il tag, Latest = tag appena pubblicato; assets Windows **e** Linux presenti

### B. Packaging Windows

- [ ] Layout **onedir**: `HostPulse.exe` + `_internal\` + `config\` (+ `baseline.json` se previsto)
- [ ] Docs dicono ancora “distribuisci l’intera cartella” (`DEPLOY.md`, `docs/WINDOWS_AV.md`)
- [ ] `SHA256.txt` nel pacchetto; ideale anche hash in body Release
- [ ] Spec: no UPX; `upx=False`; non regressare a onefile senza issue esplicita
- [ ] Firma Authenticode: solo exe → documentato; secrets CI ok se usati

### C. Packaging Linux

- [ ] `build_linux.sh` include `bin/`, `bin/ui/`, `config/` (example + baseline), `requirements.txt`, `hostpulse.sh`
- [ ] Primo avvio: venv + pip (documentare air-gap / `HOSTPULSE_PYTHON`)
- [ ] GUI: prereq `python3-tk` / display documentati; CLI resta path ufficiale headless

### D. Prodotto (engine / report / compare)

- [ ] Report HTML offline (no CDN) ancora vero
- [ ] Compare / history: score e hero = run **corrente**; scope hostname chiaro
- [ ] Profili + production-safe / quick non regressi
- [ ] Metriche Linux: gap → `PLATFORM_*_NA` / n/d, no crash

### E. Sicurezza & trust

- [ ] Nessun `shell=True` in `bin/*.py`
- [ ] Nessun secret in repo / note Release
- [ ] `PING_TARGET` e path disco non accettano input pericolosi senza validazione (migliorare se manca)

### F. Test & CI

- [ ] `pytest -q` verde in locale o CI su `main`
- [ ] Se tocchi engine/reporter/UI/packaging: piece-check in `CLAUDE.md`
- [ ] Idealmente Release non pubblica senza test (se manca gate → issue `infra`)

### G. Debt / feature scan (5–15 min)

- [ ] Issue aperte ancora valide? Chiudi o riprioritizza
- [ ] Spec prodotto (`docs/superpowers/specs/`) vs codice: gap → issue `enhancement`
- [ ] Docs agent (`CLAUDE.md`, questo file) allineati al layout reale (onedir, versioni 1.x)

**Done dell’audit:** commento su issue epic o nota in PR Release con elenco issue create/aggiornate (o “audit clean”).

---

## Come aprire issue dall’audit

```bash
gh issue create --title "…" --label "priority:high,bug" --body "$(cat <<'EOF'
## Contesto
Audit pre-release vX.Y.Z (vedi AGENT.md).

## Problema
…

## Criterio di fatto
- [ ] …
EOF
)"
```

Label usate: `bug` | `enhancement` | `documentation` | `infra` | `priority:high|medium|low` | `phase:*` se applicabile.

---

## Mappa veloce

| Path | Ruolo |
|------|--------|
| `bin/engine.py` | Collect + benchmark |
| `bin/reporter_generator.py` | HTML + slide PNG |
| `bin/ui_benchmark.py` / `bin/ui/` | GUI |
| `bin/cli.py` | Headless |
| `bin/plat.py` | Adapter OS |
| `HostPulse.windows.spec` | PyInstaller **onedir** |
| `build_exe.ps1` / `build_linux.sh` | Pacchetti release |
| `docs/graphify/` | Mappa codice per agent |

Comandi: vedi `CLAUDE.md` § Commands.

---

## DoD agent (ricordo)

- No `Co-authored-by: Cursor` nei commit
- «Fatto» solo con comando eseguito + output in sessione
- Diff minimo (ponytail); non rifattorizzare fuori scope
- Dopo cambi strutturali: `graphify update` sull’area HostPulse se disponibile

---

## Audit snapshot

Ultimo audit completo: **2026-10-20** (post `v1.4.1` + retag 1.x).  
Filtro: [`audit:2026-10-20`](https://github.com/Never-lab/hostpulse/issues?q=label%3Aaudit%3A2026-10-20).

| # | Priority | Titolo |
|---|----------|--------|
| [#42](https://github.com/Never-lab/hostpulse/issues/42) | high | Compare: scorecard = run corrente |
| [#43](https://github.com/Never-lab/hostpulse/issues/43) | high | Compare: scope stesso hostname |
| [#44](https://github.com/Never-lab/hostpulse/issues/44) | high | Windows: ship `baseline.json` |
| [#45](https://github.com/Never-lab/hostpulse/issues/45) | high | Gate tag == `version.py` |
| [#46](https://github.com/Never-lab/hostpulse/issues/46) | high | pytest prima degli asset Release |
| [#47](https://github.com/Never-lab/hostpulse/issues/47) | medium | Linux air-gap / offline |
| [#48](https://github.com/Never-lab/hostpulse/issues/48) | medium | Docs onedir + SHA256 su Release |
| [#49](https://github.com/Never-lab/hostpulse/issues/49) | medium | GUI: slides off di default |
| [#50](https://github.com/Never-lab/hostpulse/issues/50) | medium | Schema tests + fixture 1.x |
| [#51](https://github.com/Never-lab/hostpulse/issues/51) | medium | Smoke disk/chaos |
| [#52](https://github.com/Never-lab/hostpulse/issues/52) | low | Docker Windows build path |
| [#53](https://github.com/Never-lab/hostpulse/issues/53) | low | Linux GUI tk + GenericAdapter docs |
