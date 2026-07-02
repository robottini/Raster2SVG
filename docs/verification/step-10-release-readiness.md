# Step 10 Verification - Release Readiness

## Implemented

- Updated `README.md` from migration preview to release-ready project entry
  point.
- Added `CHANGELOG.md` with the initial `0.1.0` release candidate notes.
- Added `docs/legacy-python.md` to explain why the Python implementation is
  retained and what the native release actually uses.
- Added `docs/release-checklist.md` with local, manual and GitHub release
  checks.
- Marked Step 10 as completed in the migration plan.

## How to Verify

Run:

```bash
pnpm install --frozen-lockfile
cargo test --manifest-path src-tauri/Cargo.toml
pnpm run tauri:build:app
```

Then check:

```bash
du -sh src-tauri/target/release/rastersvg
du -sh src-tauri/target/release/bundle/macos/RasterSVG.app
git check-ignore -v venv node_modules src-tauri/target build dist .DS_Store
```

Expected result:

- Rust tests pass;
- macOS `.app` is generated;
- app size remains in the low single-digit MB range;
- heavy local artifacts are ignored.

Manual check:

1. Open the generated `.app` by double click.
2. Convert a real raster image.
3. Save an SVG.
4. Confirm the SVG contains vector `<path>` elements.

GitHub check:

1. Push a tag such as `v0.1.0`.
2. Confirm the `Release Desktop Packages` workflow creates draft artifacts for
   macOS and Windows.
