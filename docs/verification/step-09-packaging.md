# Step 9 Verification - Packaging macOS and Windows

## Implemented

- Added desktop icon bundle assets for macOS and Windows.
- Configured Tauri bundle icons and explicit small Windows WebView2 installer
  mode.
- Added `packageManager` metadata for reproducible pnpm setup.
- Added `tauri:build:app` for local macOS `.app` builds.
- Added GitHub Actions workflow for macOS Apple Silicon, macOS Intel and
  Windows x64 release packages.
- Documented release packaging, size expectations and signing/notarization
  tradeoffs.

## How to Verify Locally on macOS

Run:

```bash
/Users/ale/.cargo/bin/cargo test --manifest-path src-tauri/Cargo.toml
```

Then build:

```bash
PATH=/Users/ale/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:/Users/ale/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:/Users/ale/.cargo/bin:$PATH \
  /Users/ale/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pnpm exec tauri build --bundles app
```

Measure:

```bash
du -sh src-tauri/target/release/rastersvg
du -sh src-tauri/target/release/bundle/macos/RasterSVG.app
```

Expected result:

- tests pass;
- the `.app` bundle is created;
- the package remains far below 30-40 MB; the locally measured `.app` is about
  3.7 MB;
- `src-tauri/target/` may be several GB but is only local build cache.

## How to Verify on GitHub

1. Publish the repository to GitHub.
2. Open the Actions tab.
3. Run `Release Desktop Packages` manually, or push a tag such as `v0.1.0`.
4. Confirm that the release is published after all package jobs complete.
5. Confirm that macOS and Windows artifacts are attached.

Windows artifacts cannot be produced on this macOS workstation without a
Windows runner, so the GitHub Actions workflow is the verification path for
that platform.
