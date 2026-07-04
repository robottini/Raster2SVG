# RasterSVG

RasterSVG converts raster images into compact vector SVG files made of filled
paths.

[Download compiled apps](https://github.com/robottini/Raster2SVG/releases/latest)

The current primary app is a lightweight Tauri/Rust desktop application for
macOS and Windows. It keeps the existing HTML/CSS/JavaScript interface, runs
offline, and uses a native Rust pipeline with vendored Potrace 1.16 tracing.

The native desktop app does not bundle Python, NumPy, scikit-learn, scikit-image
or a virtual environment.

## Features

- Open PNG, JPEG, WebP, GIF and BMP images supported by the Rust `image` crate.
- Resize large images to a maximum working edge of 1000 px.
- Quantize colors with a deterministic K-Means pipeline.
- Apply light or aggressive smoothing before tracing.
- Exclude white or black color regions when requested.
- Trace each quantized color mask through Potrace and export filled SVG paths.
- Save the SVG locally through native desktop dialogs.

The exported SVG is a flat vector document. It does not create named SVG,
Inkscape, Illustrator or Photoshop-style layers; vector editors will see a
stack of filled `<path>` elements, usually one or more paths per traced color.

## Download and Release Builds

Compiled packages are available from the GitHub Releases page:

- [Latest release](https://github.com/robottini/Raster2SVG/releases/latest)
- [All releases](https://github.com/robottini/Raster2SVG/releases)

Current compiled packages:

- [Windows x64 installer](https://github.com/robottini/Raster2SVG/releases/download/v0.1.1/RasterSVG_0.1.1_x64-setup.exe)
- [macOS Apple Silicon app archive](https://github.com/robottini/Raster2SVG/releases/download/v0.1.1/RasterSVG_0.1.1_aarch64.app.tar.gz)
- [macOS Intel app archive](https://github.com/robottini/Raster2SVG/releases/download/v0.1.1/RasterSVG_0.1.1_x64.app.tar.gz)

Release packages are produced through GitHub Actions:

- macOS Apple Silicon `.app`;
- macOS Intel `.app`;
- Windows x64 NSIS installer.

The release workflow is defined in:

```text
.github/workflows/release.yml
```

Local macOS size measured after Step 9:

- release binary: about 3.4 MB;
- macOS `.app` bundle with icon resources: about 3.7 MB.

The local Rust build cache in `src-tauri/target/` can be several GB, but it is
ignored by Git and is not part of the release package.

## Repository Layout

- `frontend/`: shared static UI.
- `src-tauri/`: native Tauri/Rust desktop application.
- `src-tauri/vendor/potrace/`: vendored Potrace 1.16 core source.
- `backend/`: legacy Python/FastAPI backend kept as reference and fallback.
- `desktop_main.py`: legacy pywebview launcher.
- `tools/generate_legacy_baseline.py`: baseline generator for the Python
  conversion engine.
- `tests/fixtures/baseline/`: deterministic sample images.
- `tests/baseline/reference/`: legacy output reference files.
- `docs/`: migration, packaging, legacy and verification notes.

Generated artifacts such as `venv/`, `node_modules/`, `src-tauri/target/`,
`build/` and `dist/` are intentionally ignored and should not be published to
GitHub.

## Developer Setup

Install the desktop toolchain:

- Node.js;
- pnpm;
- Rust stable.

Then install JavaScript dependencies:

```bash
pnpm install
```

Run the native app in development mode:

```bash
pnpm run tauri:dev
```

Run Rust tests:

```bash
cargo test --manifest-path src-tauri/Cargo.toml
```

Build the native desktop app:

```bash
pnpm run tauri:build
```

On this Codex workstation, the exact bundled tool paths are documented in
`docs/development-environment.md`.

## Local macOS Package

To build only the macOS `.app` bundle:

```bash
pnpm run tauri:build:app
```

The output is:

```text
src-tauri/target/release/bundle/macos/RasterSVG.app
```

## Legacy Python App

The legacy Python app is retained for comparison, baseline generation and web
fallback testing. It is not required by the native release package.

Create an environment and install the legacy dependencies:

```bash
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
```

Run the legacy web app:

```bash
venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Then open:

```text
http://127.0.0.1:8000
```

More details are in `docs/legacy-python.md`.

## Baseline Verification

The baseline captures the behavior of the Python engine:

```bash
venv/bin/python tools/generate_legacy_baseline.py
```

If you only want to inspect the existing baseline:

```bash
ls tests/fixtures/baseline
ls tests/baseline/reference
sed -n '1,220p' tests/baseline/reference/manifest.json
```

## Release Checklist

Before tagging a release:

1. Run `pnpm install --frozen-lockfile`.
2. Run `cargo test --manifest-path src-tauri/Cargo.toml`.
3. Run `pnpm run tauri:build:app` on macOS.
4. Open the generated `.app` by double click.
5. Convert a real image and save an SVG.
6. Check the SVG contains vector `<path>` elements.
7. Push a tag such as `v0.1.0`.
8. Verify the draft release artifacts from GitHub Actions.

The full checklist is in `docs/release-checklist.md`.

## License

RasterSVG is licensed as GPL-2.0-or-later. See `LICENSE` and `NOTICE.md`.

This choice is intentional: the legacy implementation depends on `potracer`,
which is GPLv2+, and the native Tauri path vendors Potrace 1.16 core sources.
