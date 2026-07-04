# Release Packaging

## Goal

RasterSVG should ship as a small desktop app for macOS and Windows without a
Python runtime, virtual environment, or scientific Python libraries.

The native application uses:

- Tauri for the desktop shell;
- the static frontend in `frontend/`;
- Rust for image decoding, smoothing, quantization and SVG assembly;
- vendored Potrace 1.16 core for vector tracing.

## Local macOS Build

Run:

```bash
PATH=/Users/ale/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:/Users/ale/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:/Users/ale/.cargo/bin:$PATH \
  /Users/ale/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pnpm run tauri:build:dmg
```

Output:

```text
src-tauri/target/release/bundle/macos/RasterSVG.app
src-tauri/target/release/bundle/dmg/RasterSVG_<version>_<arch>.dmg
```

Measured after Step 9:

- release binary: about 3.4 MB;
- macOS `.app` bundle with icon resources: about 3.7 MB;
- macOS `.dmg` package: about 2 MB;
- generated icon assets in the repository: about 900 KB.

## GitHub Actions Release Build

The workflow in `.github/workflows/release.yml` builds:

- macOS Apple Silicon `.dmg`;
- macOS Intel `.dmg`;
- Windows x64 NSIS installer.

It runs on:

- manual `workflow_dispatch`;
- pushed version tags matching `v*`.

The workflow uploads build artifacts from the matrix jobs, then publishes a
GitHub release after all platform packages have been produced.

## Windows WebView2 Choice

The Windows package keeps Tauri's small installer strategy:

```json
{
  "webviewInstallMode": {
    "type": "downloadBootstrapper"
  }
}
```

This keeps the installer small. On modern Windows 10 and Windows 11 systems,
WebView2 is normally already present. On older or stripped-down systems, the
installer may download Microsoft's WebView2 bootstrapper.

If a fully offline Windows installer becomes mandatory, switch this to
`offlineInstaller`; expect roughly 127 MB more in the installer.

## Signing and Notarization

Current release builds are unsigned.

Consequences:

- macOS may show Gatekeeper warnings for downloaded builds;
- Windows may show SmartScreen warnings for unsigned installers.

Optional future work:

- add Apple Developer ID signing and notarization secrets;
- add Windows code-signing certificate secrets;
- keep unsigned local builds for development.

## References Checked

- Tauri GitHub pipeline guide:
  https://v2.tauri.app/distribute/pipelines/github/
- Tauri Windows installer guide:
  https://v2.tauri.app/distribute/windows-installer/
