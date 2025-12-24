#!/usr/bin/env bash
set -euo pipefail

# Build a macOS .app using py2app and package it into a DMG.
# Usage: build-app-and-dmg.sh [project_dir] [output_dir]

PROJECT_DIR="${1:-$(cd "$(dirname "$0")"/../.. && pwd)}"
OUTPUT_DIR="${2:-${PROJECT_DIR}/dist}"

VENV_DIR="$PROJECT_DIR/.venv-mac"

echo "Building macOS app in $PROJECT_DIR -> $OUTPUT_DIR"

rm -rf "$VENV_DIR"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip setuptools wheel
python -m pip install py2app
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
  python -m pip install -r "$PROJECT_DIR/requirements.txt"
fi

cd "$PROJECT_DIR"

echo "Running py2app (this may take a while)..."
python setup_py2app.py py2app

APP_BUNDLE="dist/main.app"
if [ ! -d "$APP_BUNDLE" ]; then
  echo "App bundle not found: $APP_BUNDLE"
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

TMPDIR=$(mktemp -d /tmp/scratchattach.app.XXXXXX)
trap 'rm -rf "$TMPDIR"' EXIT

echo "Copying app bundle to temporary dir"
cp -R "$APP_BUNDLE" "$TMPDIR/"
ln -s /Applications "$TMPDIR/Applications"

VOLNAME="Scratchattach"
DMG_PATH="$OUTPUT_DIR/${VOLNAME}.dmg"

echo "Creating DMG at $DMG_PATH"
hdiutil create -volname "$VOLNAME" -srcfolder "$TMPDIR" -ov -format UDZO "$DMG_PATH"

echo "DMG created: $DMG_PATH"
