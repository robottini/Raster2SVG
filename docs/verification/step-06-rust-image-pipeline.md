# Step 6 Verification - Pipeline immagine Rust

## Cosa e' stato implementato

Questo step aggiunge la prima parte reale del motore Rust:

- decodifica immagini con il crate Rust `image`;
- supporto iniziale per PNG, JPEG, BMP, GIF e WebP;
- resize massimo a 1000 px sul lato piu' lungo;
- K-Means RGB implementato in Rust, senza scikit-learn/scipy/OpenCV;
- palette in formato hex;
- preview SVG quantizzata a rettangoli;
- comando Tauri `convert_image_quantized`;
- fallback al placeholder solo se Tauri non ha un path file reale.

Il tracciamento vettoriale Potrace non e' ancora implementato: arrivera' nello
Step 8. Lo smoothing vero e il polish dei label arriveranno nello Step 7.

## File principali modificati

- `src-tauri/src/engine.rs`
- `src-tauri/src/lib.rs`
- `src-tauri/Cargo.toml`
- `frontend/script.js`
- `src-tauri/Cargo.lock`

## Come verificare

Dal repository:

```bash
/Users/ale/.cargo/bin/cargo test --manifest-path src-tauri/Cargo.toml
```

Atteso:

- 2 test Rust passano;
- il fixture `flat_shapes.png` viene decodificato e quantizzato;
- una preview SVG quantizzata viene generata.

## Verifica build macOS app

Usando Node/pnpm bundled di Codex e Cargo:

```bash
PATH=/Users/ale/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:/Users/ale/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:/Users/ale/.cargo/bin:$PATH \
  /Users/ale/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pnpm exec tauri build --bundles app
```

Atteso:

- viene generato `src-tauri/target/release/bundle/macos/RasterSVG.app`;
- il bundle `.app` resta molto piccolo.

Misura attuale dopo l'aggiunta del crate `image`:

```text
3.4M  src-tauri/target/release/rastersvg
3.4M  src-tauri/target/release/bundle/macos/RasterSVG.app
```

## Verifica manuale Tauri

Avvio dev:

```bash
PATH=/Users/ale/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:/Users/ale/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:/Users/ale/.cargo/bin:$PATH \
  /Users/ale/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pnpm exec tauri dev
```

Atteso:

- scegli un'immagine con il dialog nativo;
- la preview originale compare;
- "Converti in SVG" genera una preview quantizzata reale, non piu' solo
  placeholder;
- la palette mostrata deriva dalla K-Means Rust.

## Esito atteso

Se la preview quantizzata e la palette funzionano, si puo' procedere allo
Step 7: smoothing e pulizia regioni.

