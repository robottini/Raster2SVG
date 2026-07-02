# Changelog

All notable changes to RasterSVG will be documented in this file.

## 0.1.0 - Unreleased

Initial native desktop release candidate.

### Added

- Tauri 2 desktop application using the existing static frontend.
- Native Rust image pipeline for decode, resize, smoothing and K-Means color
  quantization.
- Vendored Potrace 1.16 core integration for multilayer SVG path tracing.
- Native file open/save dialogs.
- English default language on startup, with Italian still available from the
  language switcher.
- macOS `.app` local packaging.
- GitHub Actions release workflow for macOS Apple Silicon, macOS Intel and
  Windows x64.
- GPL-2.0-or-later license and Potrace notices.
- Step-by-step verification documentation.

### Kept

- Legacy Python/FastAPI backend for reference, baseline generation and fallback
  web testing.

### Known Limitations

- Release builds are unsigned, so macOS Gatekeeper and Windows SmartScreen may
  show warnings for downloaded artifacts.
- DMG packaging is optional future work; the verified macOS artifact is the
  `.app` bundle.
- Windows artifacts are produced by GitHub Actions on Windows runners, not by
  the local macOS workstation.
