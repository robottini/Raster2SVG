# Step 3 Verification - Preparazione repository open source

## Cosa e' stato implementato

Questo step prepara il repository alla pubblicazione open source:

- `.gitignore` aggiornato per Python, cache locali, Tauri, Node e pacchetti
  desktop generati;
- `.gitattributes` aggiunto per normalizzare line endings e file binari;
- `requirements.txt` trasformato in aggregatore compatibile;
- aggiunti `requirements-backend.txt`, `requirements-desktop.txt` e
  `requirements-dev.txt`;
- aggiunti `LICENSE` e `NOTICE.md`;
- README aggiornato con stato legacy, verifica baseline, roadmap e licenza.

## Come verificare

Dal repository:

```bash
git status --short
sed -n '1,220p' README.md
sed -n '1,220p' NOTICE.md
sed -n '1,120p' requirements.txt
sed -n '1,160p' .gitignore
git check-ignore -v venv build dist app.dmg app.msi
git check-ignore -v --no-index src-tauri/target/foo node_modules/foo
```

## Verifica dipendenze legacy

Se vuoi controllare che il vecchio flusso `pip install -r requirements.txt`
resti valido:

```bash
python3 -m venv /tmp/rastersvg-step3-venv
/tmp/rastersvg-step3-venv/bin/python -m pip install -r requirements.txt
/tmp/rastersvg-step3-venv/bin/python -c "import fastapi, cv2, PIL, sklearn, skimage, potrace, webview; print('legacy deps ok')"
```

Questa verifica puo' richiedere rete e tempo per scaricare pacchetti.

## Controlli attesi

- `requirements.txt` installa ancora backend, desktop shell e strumenti legacy.
- `README.md` non descrive piu' il progetto come gia' migrato.
- `LICENSE` e `NOTICE.md` dichiarano il vincolo GPL-2.0-or-later/Potrace.
- `build/`, `dist/`, `venv/` e futuri `src-tauri/target/` restano ignorati.

## Esito atteso

Se la struttura e la documentazione sono corrette, si puo' procedere allo
Step 4: scaffold Tauri minimale.
