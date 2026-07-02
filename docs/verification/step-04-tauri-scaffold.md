# Step 4 Verification - Scaffold Tauri minimale

## Cosa e' stato implementato

Questo step aggiunge uno scaffold Tauri 2 minimale:

- `package.json` con script Tauri e legacy;
- `src-tauri/Cargo.toml`;
- `src-tauri/build.rs`;
- `src-tauri/src/main.rs`;
- `src-tauri/src/lib.rs`;
- `src-tauri/tauri.conf.json`;
- `src-tauri/capabilities/default.json`.

Il frontend resta quello esistente in `frontend/`. `frontend/index.html` usa ora
asset relativi (`style.css` e `script.js`) cosi' puo' essere caricato anche da
Tauri senza server FastAPI.

Per mantenere compatibile la web app legacy, `backend/main.py` espone anche:

- `/style.css`;
- `/script.js`.

La conversione non e' ancora implementata in Tauri: questo step serve solo ad
aprire la UI desktop senza backend locale.

## Verifica senza Node/Rust

Se non hai ancora Node.js e Rust installati, puoi comunque verificare la
struttura:

```bash
python3 -m json.tool package.json > /dev/null
python3 -m json.tool src-tauri/tauri.conf.json > /dev/null
python3 -m json.tool src-tauri/capabilities/default.json > /dev/null
ls src-tauri
sed -n '1,120p' frontend/index.html
```

## Verifica legacy FastAPI

Con il venv legacy:

```bash
venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Poi apri:

```text
http://127.0.0.1:8000
```

Controlla che la pagina carichi ancora stile e JavaScript.

## Verifica Tauri

Quando Node.js, npm e Rust sono disponibili:

```bash
npm install
npm run tauri:dev
```

Atteso:

- si apre una finestra desktop RasterSVG;
- la UI mostra viewer, sidebar, lingua IT/EN e controlli;
- non serve avviare FastAPI per vedere la UI;
- il pulsante di conversione non e' ancora supportato in Tauri.

## Esito atteso

Se la UI si apre o almeno lo scaffold risulta valido, si puo' procedere allo
Step 5: bridge frontend/Tauri per file dialog, salvataggio e comando placeholder.

