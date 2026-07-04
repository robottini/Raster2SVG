#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-}"
APP_NAME="RasterSVG.app"
PRODUCT_NAME="RasterSVG"
VERSION="$(node -p "require('./package.json').version")"

if [[ -n "$TARGET" ]]; then
  BUILD_ARGS=(--target "$TARGET" --bundles app)
  TARGET_ROOT="src-tauri/target/$TARGET/release"
  case "$TARGET" in
    aarch64-apple-darwin) ARCH="aarch64" ;;
    x86_64-apple-darwin) ARCH="x64" ;;
    *) ARCH="${TARGET%%-*}" ;;
  esac
else
  BUILD_ARGS=(--bundles app)
  TARGET_ROOT="src-tauri/target/release"
  case "$(uname -m)" in
    arm64) ARCH="aarch64" ;;
    x86_64) ARCH="x64" ;;
    *) ARCH="$(uname -m)" ;;
  esac
fi

# Tauri must sign the app bundle itself before creating the DMG. Without a
# Developer ID identity this falls back to a complete ad-hoc signature, which is
# useful for local builds but still not enough for public Gatekeeper trust.
export APPLE_SIGNING_IDENTITY="${APPLE_SIGNING_IDENTITY:--}"

pnpm exec tauri build "${BUILD_ARGS[@]}"

APP_PATH="$TARGET_ROOT/bundle/macos/$APP_NAME"
DMG_DIR="$TARGET_ROOT/bundle/dmg"
DMG_PATH="$DMG_DIR/${PRODUCT_NAME}_${VERSION}_${ARCH}.dmg"

if [[ ! -d "$APP_PATH" ]]; then
  echo "Expected app bundle not found: $APP_PATH" >&2
  exit 1
fi

mkdir -p "$DMG_DIR"
rm -f "$DMG_PATH"

WORK_DIR="$(mktemp -d "${TMPDIR:-/tmp}/rastersvg-dmg.XXXXXX")"
trap 'rm -rf "$WORK_DIR"' EXIT

DMG_ROOT="$WORK_DIR/root"
mkdir -p "$DMG_ROOT"

ditto --rsrc --extattr --acl "$APP_PATH" "$DMG_ROOT/$APP_NAME"
ln -s /Applications "$DMG_ROOT/Applications"

hdiutil create \
  -volname "$PRODUCT_NAME" \
  -srcfolder "$DMG_ROOT" \
  -ov \
  -format UDZO \
  "$DMG_PATH"

if [[ "$APPLE_SIGNING_IDENTITY" != "-" ]]; then
  codesign --force --sign "$APPLE_SIGNING_IDENTITY" "$DMG_PATH"

  if [[ -n "${APPLE_ID:-}" && -n "${APPLE_PASSWORD:-}" && -n "${APPLE_TEAM_ID:-}" ]]; then
    xcrun notarytool submit "$DMG_PATH" \
      --apple-id "$APPLE_ID" \
      --password "$APPLE_PASSWORD" \
      --team-id "$APPLE_TEAM_ID" \
      --wait
    xcrun stapler staple "$DMG_PATH"
  else
    echo "Skipping DMG notarization because Apple notarization credentials are not set." >&2
  fi
fi

echo "$DMG_PATH"
