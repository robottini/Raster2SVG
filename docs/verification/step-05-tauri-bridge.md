# Step 5 Verification - Bridge frontend/Tauri

## Cosa e' stato implementato

Questo step collega la UI vanilla JavaScript a Tauri, mantenendo il fallback
browser/FastAPI:

- `frontend/script.js` rileva `window.__TAURI__`;
- apertura immagine Tauri con dialog nativo;
- lettura file immagine tramite comando Rust `read_image_file`;
- salvataggio SVG Tauri con dialog nativo e comando Rust `save_svg_file`;
- comando Rust `close_app`;
- comando Rust `convert_image_placeholder`;
- progress bar placeholder lato Tauri;
- fallback legacy invariato su `/convert` e `/status/{task_id}` quando Tauri non
  e' disponibile.

La conversione Tauri non usa ancora il motore reale: genera un SVG placeholder
deterministico. Il motore Rust vero parte dallo Step 6.

## File principali modificati

- `frontend/script.js`
- `src-tauri/src/lib.rs`
- `src-tauri/Cargo.toml`
- `src-tauri/tauri.conf.json`
- `src-tauri/capabilities/default.json`
- `package.json`

## Verifica senza Node/Rust

Se Node.js e Rust non sono ancora installati, puoi almeno validare la struttura:

```bash
python3 -m json.tool package.json > /dev/null
python3 -m json.tool src-tauri/tauri.conf.json > /dev/null
python3 -m json.tool src-tauri/capabilities/default.json > /dev/null
sed -n '1,260p' frontend/script.js
sed -n '1,260p' src-tauri/src/lib.rs
```

## Verifica legacy FastAPI

```bash
venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Apri:

```text
http://127.0.0.1:8000
```

Atteso:

- upload immagine dal browser;
- conversione tramite backend Python;
- download SVG dal browser.

## Verifica Tauri

Quando Node.js, npm e Rust sono disponibili:

```bash
npm install
npm run tauri:dev
```

In questo workspace Codex sono stati usati Node.js/pnpm bundled e Rust installato
con `rustup`. Vedi `docs/development-environment.md` per i comandi esatti.

Atteso:

- il bottone "Scegli Immagine" apre un dialog nativo;
- l'immagine scelta compare nel viewer;
- "Converti in SVG" mostra progresso e genera un SVG placeholder;
- "Scarica SVG" apre un dialog nativo e salva il file;
- "ESCI" chiude la finestra.

## Esito atteso

Se dialog, preview, placeholder e salvataggio funzionano, si puo' procedere allo
Step 6: pipeline immagine Rust per decode, resize e palette.

## Verifica gia' eseguita

In questo ambiente:

- `cargo check` passa;
- `pnpm exec tauri --version` stampa `tauri-cli 2.11.4`;
- `pnpm exec tauri build --bundles app` genera
  `src-tauri/target/release/bundle/macos/RasterSVG.app`;
- il bundle `.app` placeholder pesa circa 3.1 MB.
