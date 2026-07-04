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

macOS release jobs use Apple Developer ID signing and notarization when all
Apple secrets are configured. If those secrets are missing, the workflow falls
back to a valid ad-hoc signed DMG and publishes it with unsigned-app notes.

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

macOS release builds can be signed with a Developer ID Application certificate
and notarized by Apple. This is the only path that allows Gatekeeper to accept a
DMG downloaded from GitHub without warning that the app is damaged.

Required GitHub repository secrets for macOS release jobs:

- `APPLE_CERTIFICATE`: base64 encoded exported `.p12` Developer ID Application
  certificate;
- `APPLE_CERTIFICATE_PASSWORD`: password used when exporting the `.p12`;
- `APPLE_ID`: Apple ID email used for notarization;
- `APPLE_PASSWORD`: app-specific password for that Apple ID;
- `APPLE_TEAM_ID`: Apple Developer Team ID;
- `KEYCHAIN_PASSWORD`: temporary keychain password used only inside Actions.

The `pnpm run tauri:build:dmg` path first lets Tauri build and sign the `.app`
bundle, then creates a simple DMG that contains the app and an Applications
shortcut. When `APPLE_SIGNING_IDENTITY`, `APPLE_ID`, `APPLE_PASSWORD` and
`APPLE_TEAM_ID` are set, the script also signs and notarizes the DMG. Without a
signing identity, it defaults to Tauri ad-hoc signing and the release notes tell
macOS users how to remove the browser quarantine attribute after copying the app
to Applications.

Windows release builds are still unsigned, so Windows SmartScreen may warn until
a Windows code-signing certificate is added.

## References Checked

- Tauri GitHub pipeline guide:
  https://v2.tauri.app/distribute/pipelines/github/
- Tauri Windows installer guide:
  https://v2.tauri.app/distribute/windows-installer/
