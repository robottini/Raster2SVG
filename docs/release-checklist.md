# Release Checklist

Use this checklist before publishing a GitHub release.

## Local Checks

Run from the repository root:

```bash
pnpm install --frozen-lockfile
cargo test --manifest-path src-tauri/Cargo.toml
pnpm run tauri:build:app
```

Check expected output:

```text
src-tauri/target/release/bundle/macos/RasterSVG.app
```

Measure the local package:

```bash
du -sh src-tauri/target/release/rastersvg
du -sh src-tauri/target/release/bundle/macos/RasterSVG.app
```

Current expected size:

- release binary: about 3.4 MB;
- macOS `.app`: about 3.7 MB.

## Manual App Check

1. Open `RasterSVG.app` by double click.
2. Open a PNG, JPEG or WebP image.
3. Convert with default settings.
4. Save the SVG.
5. Open the SVG in a browser or vector editor.
6. Confirm the SVG contains `<path>` elements and no embedded raster image.
7. Repeat once with `excludeWhite` or `excludeBlack` enabled on a suitable
   image.

## Repository Check

Run:

```bash
git status --short
git check-ignore -v venv node_modules src-tauri/target build dist .DS_Store
```

Expected result:

- source changes are intentional;
- local caches and generated package folders are ignored;
- `src-tauri/target/` is not staged or committed.

## GitHub Release Check

1. Push the repository to GitHub.
2. Create a tag such as:

   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

3. Open GitHub Actions.
4. Confirm `Release Desktop Packages` succeeds for:
   - macOS Apple Silicon;
   - macOS Intel;
   - Windows x64.
5. Open the draft release.
6. Confirm all expected artifacts are attached.
7. Edit release notes if needed.
8. Publish the release.

## Optional Signing Work

Unsigned builds are acceptable for the first open-source release candidate, but
users may see platform security warnings.

Future release hardening:

- Apple Developer ID signing and notarization;
- Windows Authenticode signing;
- optional DMG packaging for macOS.
