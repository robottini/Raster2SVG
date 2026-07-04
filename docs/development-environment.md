# Development Environment

## Tooling installed/available in this workspace

Node.js and pnpm are available through the Codex bundled runtime:

```bash
/Users/ale/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --version
/Users/ale/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pnpm --version
```

Rust was installed with `rustup` using the minimal profile:

```bash
/Users/ale/.cargo/bin/rustc --version
/Users/ale/.cargo/bin/cargo --version
```

Current verified versions:

- Node.js: v24.14.0
- pnpm: 11.7.0
- rustc: 1.96.1
- cargo: 1.96.1

## PATH for Tauri commands in this Codex environment

The Codex shell does not automatically include bundled Node or Cargo. Use:

```bash
PATH=/Users/ale/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:/Users/ale/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:/Users/ale/.cargo/bin:$PATH
```

Example:

```bash
PATH=/Users/ale/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:/Users/ale/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:/Users/ale/.cargo/bin:$PATH \
  /Users/ale/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pnpm exec tauri --version
```

## Verified commands

Install JavaScript dependencies:

```bash
/Users/ale/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pnpm install
```

Check Rust/Tauri code:

```bash
/Users/ale/.cargo/bin/cargo check --manifest-path src-tauri/Cargo.toml
```

Build the macOS `.app` bundle:

```bash
PATH=/Users/ale/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:/Users/ale/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:/Users/ale/.cargo/bin:$PATH \
  /Users/ale/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pnpm exec tauri build --bundles app
```

Measured output after Step 6 image decode/resize/K-Means:

- release binary: about 3.4 MB;
- macOS `.app` bundle: about 3.4 MB.

Step 8 adds vendored Potrace tracing. Re-run the build command above and then:

```bash
du -sh src-tauri/target/release/rastersvg
du -sh src-tauri/target/release/bundle/macos/RasterSVG.app
```

Measured output after Step 9 packaging configuration:

- release binary: about 3.4 MB;
- macOS `.app` bundle with icon resources: about 3.7 MB;
- generated desktop/mobile icon assets: about 900 KB;
- local `src-tauri/target/` build cache: about 4.1 GB.

The build cache is ignored by Git and is not part of the release package.

Tauri's built-in DMG target failed in `bundle_dmg.sh` in this environment, so
the project builds the `.app` bundle and wraps it in a simple DMG with
`tools/package_macos_dmg.sh`.
