# Step 2 Verification - Baseline funzionale legacy

## Cosa viene implementato

Questo step aggiunge una baseline riproducibile dell'attuale motore Python:

- `tools/generate_legacy_baseline.py`
- immagini campione in `tests/fixtures/baseline/`
- output SVG, palette e metadati in `tests/baseline/reference/`

Lo script chiama direttamente `backend.main.process_image_task`, quindi non
avvia FastAPI, non apre finestre desktop e non richiede un browser.

## Verifica rapida senza rigenerare

Per prima cosa assicurati di essere nella cartella root del progetto:

```bash
cd /Volumes/SSD/Documents/Codex/RasterSVG
pwd
```

`pwd` deve stampare:

```text
/Volumes/SSD/Documents/Codex/RasterSVG
```

Poi puoi verificare i file gia' generati senza usare Python:

```bash
ls tests/fixtures/baseline
ls tests/baseline/reference
sed -n '1,220p' tests/baseline/reference/manifest.json
```

## Come rigenerare la baseline

Se esiste gia' `venv/bin/python`, usa:

Dal repository:

```bash
venv/bin/python tools/generate_legacy_baseline.py
```

Se ricevi `no such file or directory: venv/bin/python`, crea prima l'ambiente:

```bash
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
venv/bin/python tools/generate_legacy_baseline.py
```

In alternativa, se hai gia' un altro ambiente Python con le dipendenze di
`requirements.txt` installate, puoi usare quello.

## Controlli attesi

Dopo la verifica rapida o dopo la rigenerazione:

```bash
ls tests/fixtures/baseline
ls tests/baseline/reference
sed -n '1,220p' tests/baseline/reference/manifest.json
```

Atteso:

- 3 immagini PNG campione;
- 4 file SVG di riferimento;
- 4 file `.palette.json`;
- 4 file `.metadata.json`;
- 1 `manifest.json` con SHA, dimensioni, numero path e tempi indicativi.

Nota: i campi `duration_seconds` sono solo indicativi e possono cambiare
leggermente a ogni rigenerazione.

## Cosa controllare manualmente

- Aprire gli SVG in `tests/baseline/reference/` con un browser o un editor SVG.
- Verificare che le immagini campione siano piccole e non pesanti per GitHub.
- Verificare che questo step non modifichi `backend/`, `frontend/` o gli script
  di avvio.

## Esito atteso

Se gli output sono stati generati e sembrano coerenti, si puo' procedere allo
Step 3: preparazione del repository open source.
