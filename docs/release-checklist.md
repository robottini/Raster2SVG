# Release Checklist

Use this checklist before publishing a GitHub release.

## Local Checks

Run from the repository root:

```bash
pnpm install --frozen-lockfile
cargo test --manifest-path src-tauri/Cargo.toml
pnpm run tauri:build:dmg
```

Check expected output:

```text
src-tauri/target/release/bundle/macos/RasterSVG.app
src-tauri/target/release/bundle/dmg/RasterSVG_<version>_<arch>.dmg
```

Measure the local package:

```bash
du -sh src-tauri/target/release/rastersvg
du -sh src-tauri/target/release/bundle/macos/RasterSVG.app
```

Current expected size:

- release binary: about 3.4 MB;
- macOS `.app`: about 3.7 MB;
- macOS `.dmg`: about 2 MB.

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

1. Decide the macOS signing mode:
   - without Apple secrets, the workflow publishes ad-hoc signed DMGs;
   - with Apple Developer ID secrets, the workflow signs and notarizes DMGs.
2. Push the repository to GitHub.
3. Create a tag such as:

   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

4. Open GitHub Actions.
5. Confirm `Release Desktop Packages` succeeds for:
   - macOS Apple Silicon;
   - macOS Intel;
   - Windows x64.
6. Open the published release.
7. Confirm all expected artifacts are attached:
   - macOS Apple Silicon `.dmg`;
   - macOS Intel `.dmg`;
   - Windows x64 `.exe`.
8. Download each macOS DMG from GitHub in a browser and copy the app to
   `/Applications`.
9. For ad-hoc signed DMGs, confirm macOS may show a damaged-app warning, then
   verify the documented command opens the app:

   ```bash
   xattr -dr com.apple.quarantine /Applications/RasterSVG.app
   ```

10. For signed and notarized DMGs, confirm the copied app opens from
    `/Applications` without removing quarantine manually.
11. Edit release notes if needed.

## Optional Signing Work

Future release hardening:

- Windows Authenticode signing;
- Apple-styled DMG background and icon positioning.
