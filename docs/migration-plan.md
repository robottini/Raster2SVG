# RasterSVG Cross-Platform Migration Plan

Questo documento definisce una migrazione per checkpoint. Ogni step deve essere
verificato prima di procedere con quello successivo.

## Obiettivo finale

Creare una versione desktop multipiattaforma di RasterSVG:

- una sola codebase per macOS e Windows;
- avvio con doppio click;
- nessun ambiente virtuale Python richiesto all'utente finale;
- frontend HTML/CSS/JavaScript mantenuto il piu' vicino possibile a quello
  attuale;
- motore di conversione locale, offline e open source;
- pacchetti finali molto piu' leggeri dell'attuale bundle Python.

## Architettura target

- Shell desktop: Tauri 2.
- UI: frontend statico esistente in `frontend/`.
- Motore: Rust, con pipeline immagine equivalente all'attuale backend Python.
- Tracciamento: Potrace o integrazione compatibile con Potrace, includendo
  licenza e note di attribuzione corrette.
- Distribuzione: GitHub Actions per generare release macOS e Windows.

## Step di sviluppo

### Step 1 - Piano e criteri di verifica

Stato: completato.

Risultato:

- aggiunta documentazione di migrazione;
- definito il metodo di verifica step-by-step;
- nessuna modifica al comportamento dell'app attuale.

Verifica:

- controllare `docs/migration-plan.md`;
- controllare `docs/verification/step-01-baseline.md`;
- eseguire `git status --short`;
- opzionalmente leggere i file con `sed -n '1,220p' docs/migration-plan.md`.

### Step 2 - Baseline funzionale dell'app esistente

Stato: completato.

Risultato atteso:

- aggiungere immagini campione piccole e riproducibili;
- aggiungere uno script di test baseline che usa l'attuale backend Python;
- salvare output di riferimento: SVG, palette, metadati e tempi indicativi;
- documentare come rigenerare la baseline.

Verifica:

- eseguire lo script baseline;
- confrontare che gli SVG vengano generati;
- controllare che nessuna logica dell'app desktop venga cambiata.

### Step 3 - Preparazione repository open source

Stato: completato.

Risultato atteso:

- sistemare struttura e file ignorati per evitare `venv`, `build` e `dist`;
- separare dipendenze runtime, dev e packaging dell'app Python legacy;
- aggiungere nota licenza compatibile con Potrace;
- aggiornare README con stato "legacy Python" e roadmap Tauri.

Verifica:

- eseguire `git status --short`;
- controllare che non compaiano artefatti pesanti;
- leggere README e file licenza/note.

### Step 4 - Scaffold Tauri minimale

Stato: completato.

Risultato atteso:

- creare `src-tauri/`;
- configurare Tauri per caricare il frontend esistente;
- ottenere una finestra desktop macOS funzionante senza server FastAPI;
- nessuna conversione ancora.

Verifica:

- eseguire il comando di sviluppo Tauri;
- controllare che la UI si apra;
- verificare che layout, lingua e controlli principali siano visibili.

### Step 5 - Bridge frontend/Tauri

Stato: completato.

Risultato atteso:

- adattare `frontend/script.js` per usare Tauri quando disponibile;
- mantenere fallback browser/FastAPI per la versione legacy;
- implementare apertura immagine e salvataggio SVG con dialog nativi;
- aggiungere comando placeholder `convert_image` con progresso finto.

Verifica:

- aprire un file immagine dalla app Tauri;
- vedere anteprima e progress bar;
- salvare un SVG placeholder;
- verificare che la web app legacy continui a funzionare.

### Step 6 - Pipeline immagine in Rust: decode, resize, palette

Stato: completato.

Risultato atteso:

- decodifica PNG/JPEG/WebP dove supportato;
- resize massimo equivalente a 1000 px;
- K-Means RGB con stesso input `colors`;
- ritorno palette e immagine quantizzata;
- test unitari sul motore.

Verifica:

- eseguire test Rust;
- confrontare palette e dimensioni con baseline Python;
- controllare tempi su immagini campione.

### Step 7 - Smoothing e pulizia regioni

Stato: completato.

Risultato atteso:

- implementare smoothing light/aggressive;
- implementare median blur sui label;
- mantenere i flag `excludeWhite` ed `excludeBlack`;
- aggiornare test comparativi.

Verifica:

- convertire le immagini campione;
- controllare differenze visive rispetto alla baseline;
- verificare che bianco/nero vengano esclusi quando richiesto.

### Step 8 - Tracciamento Potrace e SVG multi-colore

Stato: completato.

Risultato atteso:

- integrare Potrace nel motore nativo;
- implementare componenti connesse;
- generare path SVG colore-per-colore come oggi;
- produrre SVG finale e palette dalla app Tauri.

Verifica:

- convertire immagini reali dalla UI;
- aprire l'SVG salvato in browser/Inkscape;
- confrontare output con baseline Python.

### Step 9 - Packaging macOS e Windows

Stato: completato.

Risultato atteso:

- configurare build release Tauri;
- aggiungere GitHub Actions;
- produrre artefatti macOS e Windows;
- documentare firma/notarizzazione opzionale.

Verifica:

- eseguire build locale macOS;
- controllare dimensione dell'artefatto;
- controllare workflow GitHub Actions.

### Step 10 - Rifinitura e rilascio

Stato: completato.

Risultato atteso:

- pulizia file legacy non piu' necessari o loro spostamento in `legacy/`;
- README finale per utenti e sviluppatori;
- changelog iniziale;
- checklist release.

Verifica:

- installazione da zero su repository pulito;
- avvio app con doppio click;
- conversione completa e salvataggio SVG;
- controllo finale dimensione pacchetto.

## Regola di avanzamento

Dopo ogni step:

1. vengono elencati i file modificati;
2. viene indicato come verificare;
3. si attende conferma prima di passare allo step successivo.
