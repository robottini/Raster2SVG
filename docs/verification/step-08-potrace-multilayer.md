# Step 8 Verification - Potrace Multilayer Tracing

## Implemented

- Vendored the minimal Potrace 1.16 core under
  `src-tauri/vendor/potrace/`.
- Compiled Potrace from the Tauri build script through the Rust `cc` crate.
- Added a Rust FFI bridge to Potrace's curve API.
- Converted each quantized palette label into a Potrace bitmap layer.
- Generated a layered SVG with one filled `<path>` per traced color.
- Updated the Tauri conversion command so the app now returns real Potrace SVG
  output instead of the temporary quantized preview.

## How to Verify from Terminal

Run:

```bash
/Users/ale/.cargo/bin/cargo test --manifest-path src-tauri/Cargo.toml
```

Expected result:

- all Rust tests pass;
- `potrace_svg_contains_layered_paths` is present in the output;
- no Python virtual environment is required.

## How to Verify from the App

1. Start the Tauri app.
2. Open a PNG/JPEG/WebP image.
3. Choose color count, smoothing, and optional white/black exclusion.
4. Convert the image.
5. Save the SVG.
6. Open the SVG in a browser or vector editor.

Expected result:

- the saved SVG contains `<path>` elements, not embedded raster data;
- the SVG comment starts with `RasterSVG Potrace multilayer output`;
- enabling white/black exclusion removes those color layers when detected.

## Verified Locally

Verified with:

```bash
/Users/ale/.cargo/bin/cargo test --manifest-path src-tauri/Cargo.toml
```

Result:

- 4 tests passed.
